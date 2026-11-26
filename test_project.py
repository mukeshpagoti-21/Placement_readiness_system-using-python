"""Unit tests covering all 15 features, data validation, safe TXT storage, and edge cases."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from exceptions import DuplicateError, FileStorageError, NotFoundError, ValidationError
from main import run_demo
from manager import PlacementManager
from reports import DEFAULT_DATA_DIR


class TestPlacementManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mgr = PlacementManager(data_dir=self.temp_dir)
        self.mgr.create_batch("B01", "Data Analytics", "Analytics", "Meera Nair")
        self.mgr.register_student(
            "STU01", "Aditi Sharma", "aditi@test.com", "9876543210", "B01"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_registration_and_validation(self):
        with self.assertRaises(DuplicateError):
            self.mgr.register_student("STU01", "Other", "other@test.com", "9876543211", "B01")
        with self.assertRaises(NotFoundError):
            self.mgr.register_student("STU02", "Test", "t@test.com", "9876543211", "NOPE")
        with self.assertRaises(ValidationError):
            self.mgr.register_student("STU02", "Test", "bad-email", "9876543211", "B01")
        with self.assertRaises(ValidationError):
            self.mgr.register_student("STU02", "Line\nBreak", "t@test.com", "9876543211", "B01")

    def test_nan_and_inf_scores_rejected(self):
        for bad in (float("nan"), float("inf"), float("-inf"), True):
            with self.assertRaises(ValidationError):
                self.mgr.record_python_score("STU01", bad, 80, 80)
            with self.assertRaises(ValidationError):
                self.mgr.record_subject_scores("STU01", sql=bad)
            with self.assertRaises(ValidationError):
                self.mgr.record_project("STU01", "Capstone", "Approved", bad)
            with self.assertRaises(ValidationError):
                self.mgr.record_mock_interview("STU01", "Cleared", tech=bad, comm=80)

    def test_atomic_score_update_and_unknown_subjects(self):
        self.mgr.record_subject_scores("STU01", sql=75, excel=80)
        with self.assertRaises(ValidationError):
            self.mgr.record_subject_scores("STU01", sql=20, excel=101)
        # SQL must remain 75 because Excel failed validation
        self.assertEqual(self.mgr.get_student("STU01").scores["sql"], 75.0)
        self.assertEqual(self.mgr.get_student("STU01").scores["excel"], 80.0)

        with self.assertRaises(ValidationError):
            self.mgr.record_subject_scores("STU01", sql=85, tableau=90)
        self.assertEqual(self.mgr.get_student("STU01").scores["sql"], 75.0)
        self.assertNotIn("tableau", self.mgr.get_student("STU01").scores)

    def test_approved_project_zero_score_not_inflated(self):
        self.mgr.record_attendance("STU01", 50, 50)
        self.mgr.record_python_score("STU01", 100, 100, 100)
        self.mgr.record_subject_scores("STU01", sql=100, excel=100, powerbi=100)
        self.mgr.record_practice("STU01", 20, 100)
        self.mgr.record_mock_interview("STU01", "Cleared", tech=100, comm=100)
        self.mgr.record_project("STU01", "Zero Graded Project", "Approved", 0.0)

        student = self.mgr.get_student("STU01")
        # 15% + 35% + 0% (project) + 10% + 15% = 75.0%
        self.assertEqual(self.mgr.calculate_overall_progress(student), 75.0)

    def test_skills_recalculated_on_downgrade(self):
        student = self.mgr.get_student("STU01")
        self.mgr.record_subject_scores("STU01", sql=90)
        self.mgr.record_project("STU01", "Capstone", "Approved", 90)
        self.mgr.record_practice("STU01", 15, 60)
        self.mgr.record_mock_interview("STU01", "Cleared", tech=85, comm=85)
        student.add_skills("Git")
        self.assertEqual(
            student.skills,
            {"SQL", "CAPSTONE", "PROBLEM_SOLVING", "INTERVIEW_READY", "GIT"},
        )

        # Downgrade metrics and verify derived skills are removed while custom skill stays
        self.mgr.record_subject_scores("STU01", sql=20)
        self.mgr.record_project("STU01", "Capstone", "In Progress", 40)
        self.mgr.record_practice("STU01", 5, 10)
        self.mgr.record_mock_interview("STU01", "Failed", tech=30, comm=40)
        self.assertEqual(student.skills, {"GIT"})

    def test_scores_progress_and_eligibility(self):
        self.mgr.record_attendance("STU01", 45, 50)
        py = self.mgr.record_python_score("STU01", 90, 90, 90)
        self.assertEqual(py, 90.0)
        self.mgr.record_subject_scores("STU01", sql=88, excel=86, powerbi=92)
        self.mgr.record_project("STU01", "Capstone", "Approved", 92)
        self.mgr.record_practice("STU01", 20, 100)
        self.mgr.record_mock_interview("STU01", "Cleared", tech=88, comm=86)

        student = self.mgr.get_student("STU01")
        progress = self.mgr.calculate_overall_progress(student)
        self.assertGreaterEqual(progress, 85.0)
        self.assertEqual(self.mgr.get_performance_category(student), "Platinum")
        eligible, reasons = self.mgr.check_placement_eligibility(student)
        self.assertTrue(eligible)
        self.assertEqual(reasons, [])

    def test_search_top_and_improvement(self):
        self.mgr.record_attendance("STU01", 45, 50)
        self.mgr.record_python_score("STU01", 90, 90, 90)
        self.mgr.record_subject_scores("STU01", sql=90, excel=85, powerbi=85)
        self.mgr.record_project("STU01", "Capstone", "Approved", 90)
        self.mgr.record_practice("STU01", 20, 80)
        self.mgr.record_mock_interview("STU01", "Cleared", tech=85, comm=85)

        self.mgr.register_student("STU02", "Deepak Joshi", "deepak@test.com", "9876543219", "B01")
        self.mgr.record_attendance("STU02", 25, 50)

        self.assertEqual(len(self.mgr.search_students("aditi", by="name")), 1)
        top = self.mgr.get_top_performers(n=1, batch_id="B01")
        self.assertEqual(top[0][0].student_id, "STU01")

        flagged = self.mgr.get_students_needing_improvement()
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0][0].student_id, "STU02")

    def test_delimiter_protection_and_roundtrip(self):
        self.mgr.create_batch("B02", "Data | AI, 2026", "AI & ML", "Ravi, Rao")
        self.mgr.register_student("STU02", "Kiran~Patel", "kiran@test.com", "9876543215", "B02")
        self.mgr.record_project("STU02", "Sales~Dashboard, v1|2", "Submitted", 80)
        self.mgr.save_data()

        reloaded = PlacementManager(data_dir=self.temp_dir)
        reloaded.load_data()
        self.assertEqual(reloaded.batches["B02"].name, "Data | AI, 2026")
        s2 = reloaded.get_student("STU02")
        self.assertEqual(s2.project["title"], "Sales~Dashboard, v1|2")
        self.assertEqual(s2.name, "Kiran~Patel")

    def test_load_validation_rejects_corrupted_records(self):
        self.mgr.save_data()

        # 1. Truncated student record
        with open(self.mgr.storage.students_file, "w", encoding="utf-8") as f:
            f.write("STU01|Aditi|aditi@test.com\n")
        with self.assertRaises(FileStorageError):
            PlacementManager(data_dir=self.temp_dir).load_data()

        # 2. Student referencing nonexistent batch
        self.mgr.save_data()
        with open(self.mgr.storage.batches_file, "w", encoding="utf-8") as f:
            f.write("B99|Other|Track|Coach\n")
        with self.assertRaises(FileStorageError):
            PlacementManager(data_dir=self.temp_dir).load_data()

    def test_safe_save_preserves_previous_valid_dataset_on_failure(self):
        self.mgr.record_attendance("STU01", 40, 50)
        self.mgr.save_data()

        # Modify in memory and simulate a failure during file swap
        self.mgr.record_attendance("STU01", 45, 50)
        with patch("reports.os.replace", side_effect=OSError("disk error")):
            with self.assertRaises(FileStorageError):
                self.mgr.save_data()

        # Previous valid dataset on disk (40/50 -> 80%) must remain intact
        reloaded = PlacementManager(data_dir=self.temp_dir)
        reloaded.load_data()
        self.assertEqual(reloaded.get_student("STU01").attendance_pct, 80.0)

    def test_default_data_dir_relative_to_app_and_demo_isolated(self):
        # Even from another working directory, default storage resolves to APP_DIR/data
        old_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            mgr_default = PlacementManager()
            self.assertEqual(mgr_default.storage.base_dir, DEFAULT_DATA_DIR)
        finally:
            os.chdir(old_cwd)

        # Running demo in a separate directory leaves live data folder untouched
        live_batches = os.path.join(self.temp_dir, "live")
        demo_dir = os.path.join(self.temp_dir, "demo")
        live_mgr = PlacementManager(data_dir=live_batches)
        live_mgr.create_batch("LIVE1", "Live Batch", "Python", "Coach")
        live_mgr.register_student("LIVE99", "Live Student", "live@test.com", "9999999999", "LIVE1")
        live_mgr.save_data()

        run_demo(demo_dir=demo_dir)

        check_live = PlacementManager(data_dir=live_batches)
        check_live.load_data()
        self.assertIn("LIVE99", check_live.students)
        self.assertTrue(os.path.exists(os.path.join(demo_dir, "reports", "student_STU101.txt")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
