"""Core PlacementManager coordinating all 15 features in a clean, simple API."""

from typing import Dict, List, Optional, Tuple

from exceptions import DuplicateError, NotFoundError, ValidationError
from models import WEIGHTS, Batch, Student
from reports import StudentReport, SummaryReport, TxtStorage


class PlacementManager:
    """Manages batches, student progress, placement readiness, and TXT storage."""

    def __init__(self, data_dir: Optional[str] = None):
        self.batches: Dict[str, Batch] = {}
        self.students: Dict[str, Student] = {}
        self.storage = TxtStorage(data_dir)

    # 1. Batch Management
    def create_batch(self, batch_id: str, name: str, track: str, instructor: str) -> Batch:
        key = batch_id.strip().upper()
        if key in self.batches:
            raise DuplicateError(f"Batch '{key}' already exists.")
        batch = Batch(key, name, track, instructor)
        self.batches[key] = batch
        return batch

    def get_batch_students(self, batch_id: str) -> List[Student]:
        key = batch_id.strip().upper()
        if key not in self.batches:
            raise NotFoundError(f"Batch '{key}' not found.")
        return [
            self.students[sid]
            for sid in sorted(self.batches[key].student_ids)
            if sid in self.students
        ]

    # 2. Student Registration
    def register_student(
        self, student_id: str, name: str, email: str, phone: str, batch_id: str
    ) -> Student:
        sid = student_id.strip().upper()
        bid = batch_id.strip().upper()
        if sid in self.students:
            raise DuplicateError(f"Student '{sid}' already exists.")
        if bid not in self.batches:
            raise NotFoundError(f"Batch '{bid}' not found. Create the batch first.")

        student = Student(sid, name, email, phone, bid)
        self.students[sid] = student
        self.batches[bid].add_student(sid)
        return student

    def get_student(self, student_id: str) -> Student:
        sid = student_id.strip().upper()
        if sid not in self.students:
            raise NotFoundError(f"Student '{sid}' not found.")
        return self.students[sid]

    # 3. Attendance Tracking
    def record_attendance(self, student_id: str, attended: int, total: int) -> float:
        student = self.get_student(student_id)
        student.update_attendance(attended, total)
        return student.attendance_pct

    # 4. Python Assessment Scores
    def record_python_score(
        self, student_id: str, theory: float, coding: float, mcq: float
    ) -> float:
        student = self.get_student(student_id)
        return student.update_python_score(theory, coding, mcq)

    # 5. Manual SQL / Excel / Power BI Score Entry (*args & **kwargs)
    def record_subject_scores(
        self, student_id: str, *args: float, **kwargs: float
    ) -> Dict[str, float]:
        student = self.get_student(student_id)
        student.update_scores(*args, **kwargs)
        return student.scores

    # 6. Project Completion Status
    def record_project(
        self, student_id: str, title: str, status: str, score: float = 0.0
    ) -> dict:
        student = self.get_student(student_id)
        student.update_project(title, status, score)
        return student.project

    # 7. Practice Session Tracking
    def record_practice(
        self, student_id: str, sessions: int, problems_solved: int
    ) -> dict:
        student = self.get_student(student_id)
        student.update_practice(sessions, problems_solved)
        return student.practice

    # 8. Mock Interview Status
    def record_mock_interview(
        self, student_id: str, status: str, tech: float = 0.0, comm: float = 0.0
    ) -> dict:
        student = self.get_student(student_id)
        student.update_mock_interview(status, tech, comm)
        return student.mock_interview

    # 9. Overall Progress Percentage
    def calculate_overall_progress(self, student: Student) -> float:
        att_score = student.attendance_pct
        scores = student.scores.values()
        tech_avg = sum(scores) / len(student.scores) if student.scores else 0.0

        proj = student.project
        if proj["status"] == "Approved":
            # Use the actual graded score (0 remains 0, never treated as missing data)
            proj_score = proj["score"]
        elif proj["status"] == "Submitted":
            proj_score = min(85.0, proj["score"])
        elif proj["status"] == "In Progress":
            proj_score = 40.0
        else:
            proj_score = 0.0

        practice_score = min(100.0, float(student.practice["problems_solved"]))  # target = 100

        mock = student.mock_interview
        if mock["status"] == "Cleared":
            mock_score = (mock["tech"] + mock["comm"]) / 2
        elif mock["status"] == "Scheduled":
            mock_score = 40.0
        elif mock["status"] == "Failed":
            mock_score = 20.0
        else:
            mock_score = 0.0

        components = {
            "attendance": att_score,
            "assessments": tech_avg,
            "project": proj_score,
            "practice": practice_score,
            "mock": mock_score,
        }
        total = sum(components[name] * weight for name, weight in WEIGHTS)
        return round(total, 2)

    # 10. Performance Category
    def get_performance_category(self, student: Student) -> str:
        progress = self.calculate_overall_progress(student)
        if (
            progress >= 85
            and student.attendance_pct >= 80
            and student.project["status"] == "Approved"
        ):
            return "Platinum"
        if progress >= 75:
            return "Gold"
        if progress >= 60:
            return "Silver"
        return "Bronze"

    # 11. Placement Eligibility Check
    def check_placement_eligibility(self, student: Student) -> Tuple[bool, List[str]]:
        reasons: List[str] = []
        avg_score = sum(student.scores.values()) / len(student.scores)

        if student.attendance_pct < 80:
            reasons.append(f"Attendance {student.attendance_pct}% < 80%")
        if avg_score < 70:
            reasons.append(f"Technical average {avg_score:.1f}% < 70%")
        if student.project["status"] != "Approved":
            reasons.append(
                f"Project status is '{student.project['status']}' (needs 'Approved')"
            )
        if student.mock_interview["status"] != "Cleared":
            reasons.append(
                f"Mock interview is '{student.mock_interview['status']}' (needs 'Cleared')"
            )
        if student.practice["problems_solved"] < 50:
            reasons.append(
                f"Practice problems {student.practice['problems_solved']} < 50"
            )

        return (len(reasons) == 0, reasons)

    # 12. Student Search
    def search_students(self, query: str, by: str = "name") -> List[Student]:
        q = query.strip().lower()
        mode = by.strip().lower()
        if mode == "id":
            return [s for s in self.students.values() if q in s.student_id.lower()]
        if mode == "batch":
            return [s for s in self.students.values() if q in s.batch_id.lower()]
        if mode == "category":
            return [
                s
                for s in self.students.values()
                if q in self.get_performance_category(s).lower()
            ]
        return [s for s in self.students.values() if q in s.name.lower()]

    # 13. Top Performer Identification
    def get_top_performers(
        self, n: int = 3, batch_id: Optional[str] = None
    ) -> List[Tuple[Student, float, str]]:
        if n < 0:
            raise ValidationError("Count 'n' cannot be negative.")
        pool = (
            self.get_batch_students(batch_id)
            if batch_id
            else list(self.students.values())
        )
        ranked = sorted(
            [
                (
                    s,
                    self.calculate_overall_progress(s),
                    self.get_performance_category(s),
                )
                for s in pool
            ],
            key=lambda item: item[1],
            reverse=True,
        )
        return ranked[:n]

    # 14. Students Needing Improvement
    def get_students_needing_improvement(self) -> List[Tuple[Student, float, List[str]]]:
        flagged = []
        for student in self.students.values():
            progress = self.calculate_overall_progress(student)
            eligible, reasons = self.check_placement_eligibility(student)
            if not eligible or progress < 60:
                flagged.append((student, progress, reasons))
        return sorted(flagged, key=lambda item: item[1])

    # Set Operations Helper (Union, Intersection)
    def analyze_batch_skills(self, batch_id: str) -> Dict[str, set]:
        students = self.get_batch_students(batch_id)
        if not students:
            return {"all_skills": set(), "common_skills": set()}
        skill_sets = [s.skills for s in students]
        all_skills = set().union(*skill_sets)
        common_skills = skill_sets[0].intersection(*skill_sets[1:])
        return {"all_skills": all_skills, "common_skills": common_skills}

    # 15. Simple TXT-Based Storage & Report Export
    def save_data(self) -> None:
        self.storage.save_all(self.batches, self.students)

    def load_data(self) -> None:
        self.batches, self.students = self.storage.load_all()

    def export_student_report(self, student_id: str) -> str:
        student = self.get_student(student_id)
        progress = self.calculate_overall_progress(student)
        category = self.get_performance_category(student)
        eligible, reasons = self.check_placement_eligibility(student)
        report = StudentReport(student, progress, category, eligible, reasons)
        return self.storage.save_report(f"student_{student.student_id}.txt", report)

    def export_summary_report(self, batch_id: Optional[str] = None) -> str:
        pool = (
            self.get_batch_students(batch_id)
            if batch_id
            else list(self.students.values())
        )
        rows = [
            (
                s,
                self.calculate_overall_progress(s),
                self.get_performance_category(s),
                self.check_placement_eligibility(s)[0],
            )
            for s in sorted(pool, key=lambda x: x.student_id)
        ]
        title = (
            f"BATCH SUMMARY: {batch_id.upper()}"
            if batch_id
            else "PLACEMENT READINESS SUMMARY"
        )
        filename = (
            f"batch_{batch_id.upper()}.txt" if batch_id else "placement_summary.txt"
        )
        return self.storage.save_report(filename, SummaryReport(title, rows))
