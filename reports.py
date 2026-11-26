"""TXT-based reporting (Inheritance & Polymorphism) and safe TXT file persistence."""

import os
import shutil
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from exceptions import FileStorageError, PlacementError
from models import CORE_SUBJECTS, Batch, Student, validate_score

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.join(APP_DIR, "data")

_ESCAPE_MAP = (
    ("%", "%25"),
    ("|", "%7C"),
    ("~", "%7E"),
    (",", "%2C"),
    ("\n", "%0A"),
    ("\r", "%0D"),
)


def _escape(text: str) -> str:
    """Escape reserved TXT delimiters before writing."""
    result = text
    for raw, token in _ESCAPE_MAP:
        result = result.replace(raw, token)
    return result


def _unescape(text: str) -> str:
    """Restore escaped TXT delimiters after reading."""
    result = text
    for raw, token in reversed(_ESCAPE_MAP):
        result = result.replace(token, raw)
    return result


class ReportGenerator(ABC):
    """Abstract base class for polymorphic TXT report generation."""

    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def generate(self) -> str:
        """Return formatted text report content."""


class StudentReport(ReportGenerator):
    """Generates a clean TXT progress dossier for a single student."""

    def __init__(
        self,
        student: Student,
        progress: float,
        category: str,
        eligible: bool,
        reasons: List[str],
    ):
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
    """Handles safe atomic TXT record persistence and TXT report export."""

    def __init__(self, base_dir: Optional[str] = None):
        resolved_dir = os.path.abspath(base_dir) if base_dir is not None else DEFAULT_DATA_DIR
        self.base_dir = resolved_dir
        self.reports_dir = os.path.join(self.base_dir, "reports")
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        self.batches_file = os.path.join(self.base_dir, "batches.txt")
        self.students_file = os.path.join(self.base_dir, "students.txt")

    def _serialize_batches(self, batches: Dict[str, Batch]) -> str:
        lines = []
        for b in batches.values():
            lines.append(
                "|".join(
                    (
                        _escape(b.batch_id),
                        _escape(b.name),
                        _escape(b.track),
                        _escape(b.instructor),
                    )
                )
            )
        return "\n".join(lines) + ("\n" if lines else "")

    def _serialize_students(self, batches: Dict[str, Batch], students: Dict[str, Student]) -> str:
        lines = []
        for s in students.values():
            if s.batch_id not in batches:
                raise FileStorageError(
                    f"Cannot save student '{s.student_id}': batch '{s.batch_id}' does not exist."
                )
            scores_str = ",".join(f"{k}:{s.scores[k]}" for k in CORE_SUBJECTS)
            py = s.python_parts
            att = s.attendance
            proj = s.project
            prac = s.practice
            mock = s.mock_interview
            skills_str = ",".join(_escape(sk) for sk in sorted(s.skills))
            fields = [
                _escape(s.student_id),
                _escape(s.name),
                _escape(s.email),
                _escape(s.phone),
                _escape(s.batch_id),
                f"{att['attended']}/{att['total']}",
                f"{py['theory']},{py['coding']},{py['mcq']}",
                scores_str,
                f"{_escape(proj['title'])}~{_escape(proj['status'])}~{proj['score']}",
                f"{prac['sessions']},{prac['problems_solved']}",
                f"{_escape(mock['status'])}~{mock['tech']}~{mock['comm']}",
                skills_str,
            ]
            lines.append("|".join(fields))
        return "\n".join(lines) + ("\n" if lines else "")

    @staticmethod
    def _parse_batches_lines(lines: List[str]) -> Dict[str, Batch]:
        batches: Dict[str, Batch] = {}
        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                continue
            parts = line.split("|")
            if len(parts) != 4:
                raise FileStorageError(
                    f"batches.txt line {line_no}: expected 4 fields, got {len(parts)}."
                )
            batch_id, name, track, instructor = (_unescape(p) for p in parts)
            batch = Batch(batch_id, name, track, instructor)
            if batch.batch_id in batches:
                raise FileStorageError(
                    f"batches.txt line {line_no}: duplicate batch ID '{batch.batch_id}'."
                )
            batches[batch.batch_id] = batch
        return batches

    @staticmethod
    def _parse_students_lines(
        lines: List[str], batches: Dict[str, Batch]
    ) -> Dict[str, Student]:
        students: Dict[str, Student] = {}
        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                continue
            parts = line.split("|")
            if len(parts) != 12:
                raise FileStorageError(
                    f"students.txt line {line_no}: expected 12 fields, got {len(parts)}."
                )

            sid, name, email, phone, bid = (_unescape(p) for p in parts[:5])
            student = Student(sid, name, email, phone, bid)
            if student.student_id in students:
                raise FileStorageError(
                    f"students.txt line {line_no}: duplicate student ID '{student.student_id}'."
                )
            if student.batch_id not in batches:
                raise FileStorageError(
                    f"students.txt line {line_no}: student '{student.student_id}' references unknown batch '{student.batch_id}'."
                )

            # Attendance: attended/total
            att_parts = parts[5].split("/")
            if len(att_parts) != 2:
                raise FileStorageError(
                    f"students.txt line {line_no}: invalid attendance format '{parts[5]}'."
                )
            attended, total = int(att_parts[0]), int(att_parts[1])
            if total == 0:
                if attended != 0:
                    raise FileStorageError(
                        f"students.txt line {line_no}: attended ({attended}) > total (0)."
                    )
            else:
                student.update_attendance(attended, total)

            # Python breakdown: theory,coding,mcq
            py_parts = parts[6].split(",")
            if len(py_parts) != 3:
                raise FileStorageError(
                    f"students.txt line {line_no}: invalid Python score breakdown."
                )
            t, c, m = (validate_score(x, "Python Part") for x in py_parts)
            if any((t, c, m)):
                student.update_python_score(t, c, m)

            # Core subject scores: python:..,sql:..,excel:..,powerbi:..
            score_pairs = [p for p in parts[7].split(",") if p]
            score_map: Dict[str, float] = {}
            for pair in score_pairs:
                if ":" not in pair:
                    raise FileStorageError(
                        f"students.txt line {line_no}: invalid score entry '{pair}'."
                    )
                k, v = pair.split(":", 1)
                if k in score_map:
                    raise FileStorageError(
                        f"students.txt line {line_no}: duplicate subject '{k}'."
                    )
                score_map[k] = float(v)
            if set(score_map.keys()) != set(CORE_SUBJECTS):
                raise FileStorageError(
                    f"students.txt line {line_no}: expected scores for {CORE_SUBJECTS}, got {tuple(score_map.keys())}."
                )
            student.update_scores(**score_map)

            # Project: title~status~score
            proj_parts = parts[8].split("~")
            if len(proj_parts) != 3:
                raise FileStorageError(
                    f"students.txt line {line_no}: invalid project format."
                )
            ptitle, pstatus, pscore = _unescape(proj_parts[0]), _unescape(proj_parts[1]), float(proj_parts[2])
            student.update_project(ptitle, pstatus, pscore)

            # Practice: sessions,problems
            prac_parts = parts[9].split(",")
            if len(prac_parts) != 2:
                raise FileStorageError(
                    f"students.txt line {line_no}: invalid practice format."
                )
            sessions, problems = int(prac_parts[0]), int(prac_parts[1])
            student.update_practice(sessions, problems)

            # Mock interview: status~tech~comm
            mock_parts = parts[10].split("~")
            if len(mock_parts) != 3:
                raise FileStorageError(
                    f"students.txt line {line_no}: invalid mock interview format."
                )
            mstatus, mtech, mcomm = _unescape(mock_parts[0]), float(mock_parts[1]), float(mock_parts[2])
            student.update_mock_interview(mstatus, mtech, mcomm)

            # Skills (derived skills are synced from state; custom tags are restored)
            if parts[11]:
                raw_skills = [_unescape(sk) for sk in parts[11].split(",") if sk]
                student.add_skills(*raw_skills)

            students[student.student_id] = student
            batches[student.batch_id].add_student(student.student_id)

        return students

    def save_all(self, batches: Dict[str, Batch], students: Dict[str, Student]) -> None:
        """Validate, stage to temp files, keep recoverable backups, and swap atomically."""
        batches_tmp = self.batches_file + ".tmp"
        students_tmp = self.students_file + ".tmp"
        batches_bak = self.batches_file + ".bak"
        students_bak = self.students_file + ".bak"

        batches_text = self._serialize_batches(batches)
        students_text = self._serialize_students(batches, students)

        # Verify serialized output parses back cleanly before touching disk state
        parsed_batches = self._parse_batches_lines(batches_text.splitlines())
        self._parse_students_lines(students_text.splitlines(), parsed_batches)

        had_batches = os.path.exists(self.batches_file)
        had_students = os.path.exists(self.students_file)
        replaced_batches = False

        try:
            with open(batches_tmp, "w", encoding="utf-8") as f:
                f.write(batches_text)
                f.flush()
                os.fsync(f.fileno())

            with open(students_tmp, "w", encoding="utf-8") as f:
                f.write(students_text)
                f.flush()
                os.fsync(f.fileno())

            # Validate temp files read back from disk
            with open(batches_tmp, "r", encoding="utf-8") as f:
                verified_batches = self._parse_batches_lines(f.readlines())
            with open(students_tmp, "r", encoding="utf-8") as f:
                self._parse_students_lines(f.readlines(), verified_batches)

            # Keep recoverable backups of previous valid dataset
            if had_batches:
                shutil.copy2(self.batches_file, batches_bak)
            if had_students:
                shutil.copy2(self.students_file, students_bak)

            os.replace(batches_tmp, self.batches_file)
            replaced_batches = True
            os.replace(students_tmp, self.students_file)
        except (OSError, ValueError, PlacementError) as exc:
            # Roll back if batches.txt was replaced before students.txt failed
            if replaced_batches and had_batches and os.path.exists(batches_bak):
                try:
                    shutil.copy2(batches_bak, self.batches_file)
                except OSError:
                    pass
            raise FileStorageError(f"Failed to save data safely: {exc}") from exc
        finally:
            for tmp_path in (batches_tmp, students_tmp):
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

    def load_all(self) -> Tuple[Dict[str, Batch], Dict[str, Student]]:
        """Load and strictly validate batches and students from TXT storage."""
        try:
            batches: Dict[str, Batch] = {}
            if os.path.exists(self.batches_file):
                with open(self.batches_file, "r", encoding="utf-8") as f:
                    batches = self._parse_batches_lines(f.readlines())

            students: Dict[str, Student] = {}
            if os.path.exists(self.students_file):
                with open(self.students_file, "r", encoding="utf-8") as f:
                    students = self._parse_students_lines(f.readlines(), batches)

            return batches, students
        except FileStorageError:
            raise
        except (OSError, ValueError, PlacementError) as exc:
            raise FileStorageError(f"Failed to load saved data: {exc}") from exc

    def save_report(self, filename: str, report: ReportGenerator) -> str:
        """Save any ReportGenerator output polymorphically to a TXT file."""
        path = os.path.join(self.reports_dir, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report.generate() + "\n")
            return path
        except OSError as exc:
            raise FileStorageError(f"Failed to write report '{filename}': {exc}") from exc
