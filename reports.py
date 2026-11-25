"""TXT-based reporting (Inheritance & Polymorphism) and simple TXT file persistence."""

import os
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from exceptions import FileStorageError
from models import Batch, Student


class ReportGenerator(ABC):
    """Abstract base class for polymorphic TXT report generation."""

    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def generate(self) -> str:
        """Return formatted text report content."""


class StudentReport(ReportGenerator):
    """Generates a clean TXT progress dossier for a single student."""

    def __init__(self, student: Student, progress: float, category: str,
                 eligible: bool, reasons: List[str]):
        super().__init__(f"STUDENT REPORT: {student.student_id}")
        self.student = student
        self.progress = progress
        self.category = category
        self.eligible = eligible
        self.reasons = reasons

    def generate(self) -> str:
        s = self.student
        lines = [
            "=" * 60,
            self.title.center(60),
            "=" * 60,
            f"Name            : {s.name}",
            f"Batch           : {s.batch_id}",
            f"Email / Phone   : {s.email} | {s.phone}",
            f"Attendance      : {s.attendance['attended']}/{s.attendance['total']} ({s.attendance_pct}%)",
            f"Scores          : {s.scores}",
            f"Project         : {s.project['title']} [{s.project['status']}] ({s.project['score']}%)",
            f"Practice        : {s.practice['sessions']} sessions, {s.practice['problems_solved']} problems",
            f"Mock Interview  : {s.mock_interview['status']} (Tech: {s.mock_interview['tech']}, Comm: {s.mock_interview['comm']})",
            f"Skills          : {', '.join(sorted(s.skills)) or 'None'}",
            "-" * 60,
            f"Overall Progress: {self.progress}%",
            f"Category        : {self.category}",
            f"Placement Ready : {'YES' if self.eligible else 'NO'}",
        ]
        if self.reasons:
            lines.append("Gaps to Address :")
            lines.extend(f"  - {reason}" for reason in self.reasons)
        lines.append("=" * 60)
        return "\n".join(lines)


class SummaryReport(ReportGenerator):
    """Generates an institute-wide or batch-wide placement readiness summary."""

    def __init__(self, title: str, rows: List[Tuple[Student, float, str, bool]]):
        super().__init__(title)
        self.rows = rows

    def generate(self) -> str:
        lines = [
            "=" * 78,
            self.title.center(78),
            "=" * 78,
            f"{'ID':<8} {'Name':<18} {'Batch':<10} {'Att%':>6} {'Score%':>7} {'Category':<14} {'Eligible':<8}",
            "-" * 78,
        ]
        for student, score, category, eligible in self.rows:
            status = "Yes" if eligible else "No"
            lines.append(
                f"{student.student_id:<8} {student.name:<18} {student.batch_id:<10} "
                f"{student.attendance_pct:>5.1f}% {score:>6.1f}% {category:<14} {status:<8}"
            )
        lines.append("=" * 78)
        return "\n".join(lines)


class TxtStorage:
    """Handles saving/loading records and writing TXT reports."""

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        self.batches_file = os.path.join(self.base_dir, "batches.txt")
        self.students_file = os.path.join(self.base_dir, "students.txt")

    def save_all(self, batches: Dict[str, Batch], students: Dict[str, Student]) -> None:
        try:
            with open(self.batches_file, "w", encoding="utf-8") as f:
                for b in batches.values():
                    f.write(f"{b.batch_id}|{b.name}|{b.track}|{b.instructor}\n")

            with open(self.students_file, "w", encoding="utf-8") as f:
                for s in students.values():
                    scores_str = ",".join(f"{k}:{v}" for k, v in s.scores.items())
                    py = s.python_parts
                    att = s.attendance
                    proj = s.project
                    prac = s.practice
                    mock = s.mock_interview
                    skills_str = ",".join(sorted(s.skills))
                    fields = [
                        s.student_id, s.name, s.email, s.phone, s.batch_id,
                        f"{att['attended']}/{att['total']}",
                        f"{py['theory']},{py['coding']},{py['mcq']}",
                        scores_str,
                        f"{proj['title']}~{proj['status']}~{proj['score']}",
                        f"{prac['sessions']},{prac['problems_solved']}",
                        f"{mock['status']}~{mock['tech']}~{mock['comm']}",
                        skills_str,
                    ]
                    f.write("|".join(fields) + "\n")
        except OSError as exc:
            raise FileStorageError(f"Failed to save data: {exc}") from exc

    def load_all(self) -> Tuple[Dict[str, Batch], Dict[str, Student]]:
        batches: Dict[str, Batch] = {}
        students: Dict[str, Student] = {}
        try:
            if os.path.exists(self.batches_file):
                with open(self.batches_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        batch_id, name, track, instructor = line.split("|")
                        batches[batch_id] = Batch(batch_id, name, track, instructor)

            if os.path.exists(self.students_file):
                with open(self.students_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split("|")
                        sid, name, email, phone, bid = parts[:5]
                        student = Student(sid, name, email, phone, bid)

                        attended, total = (int(x) for x in parts[5].split("/"))
                        if total > 0:
                            student.update_attendance(attended, total)

                        t, c, m = (float(x) for x in parts[6].split(","))
                        if any((t, c, m)):
                            student.update_python_score(t, c, m)

                        score_map = {}
                        for pair in parts[7].split(","):
                            if ":" in pair:
                                k, v = pair.split(":", 1)
                                score_map[k] = float(v)
                        student.update_scores(**score_map)

                        ptitle, pstatus, pscore = parts[8].split("~")
                        student.update_project(ptitle, pstatus, float(pscore))

                        sessions, problems = (int(x) for x in parts[9].split(","))
                        student.update_practice(sessions, problems)

                        mstatus, mtech, mcomm = parts[10].split("~")
                        student.update_mock_interview(mstatus, float(mtech), float(mcomm))

                        if len(parts) > 11 and parts[11]:
                            student.add_skills(*parts[11].split(","))

                        students[student.student_id] = student
                        if bid in batches:
                            batches[bid].add_student(student.student_id)
        except (OSError, ValueError) as exc:
            raise FileStorageError(f"Failed to load data: {exc}") from exc

        return batches, students

    def save_report(self, filename: str, report: ReportGenerator) -> str:
        """Save any ReportGenerator output polymorphically to a TXT file."""
        path = os.path.join(self.reports_dir, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report.generate() + "\n")
            return path
        except OSError as exc:
            raise FileStorageError(f"Failed to write report '{filename}': {exc}") from exc
