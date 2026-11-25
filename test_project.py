"""Unit tests covering all 15 features and TXT persistence."""

import shutil
import tempfile
import unittest

from exceptions import DuplicateError, NotFoundError, ValidationError
from manager import PlacementManager


class TestPlacementManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mgr = PlacementManager(data_dir=self.temp_dir)
        self.mgr.create_batch("B01", "Data Analytics", "Analytics", "Meera Nair")
        self.mgr.register_student("STU01", "Aditi Sharma", "aditi@test.com", "9876543210", "B01")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_registration_and_validation(self):
        with self.assertRaises(DuplicateError):
            self.mgr.register_student("STU01", "Other", "other@test.com", "9876543211", "B01")
        with self.assertRaises(NotFoundError):
            self.mgr.register_student("STU02", "Test", "t@test.com", "9876543211", "NOPE")
        with self.assertRaises(ValidationError):
            self.mgr.register_student("STU02", "Test", "bad-email", "9876543211", "B01")

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

    def test_txt_persistence_and_reports(self):
        self.mgr.record_attendance("STU01", 40, 50)
        self.mgr.record_subject_scores("STU01", 80, 82, 84, 86)  # *args test
        self.mgr.save_data()

        reloaded = PlacementManager(data_dir=self.temp_dir)
        reloaded.load_data()
        student = reloaded.get_student("STU01")
        self.assertEqual(student.attendance_pct, 80.0)
        self.assertEqual(student.scores["powerbi"], 86.0)

        report_path = reloaded.export_student_report("STU01")
        summary_path = reloaded.export_summary_report()
        with open(report_path, "r", encoding="utf-8") as f:
            self.assertIn("STUDENT REPORT: STU01", f.read())
        with open(summary_path, "r", encoding="utf-8") as f:
            self.assertIn("PLACEMENT READINESS SUMMARY", f.read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
