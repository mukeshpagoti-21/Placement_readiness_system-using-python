"""Domain models demonstrating OOP (Classes, Encapsulation, Inheritance, Polymorphism)
alongside Tuples, Sets, Dictionaries, Lists, Strings, and *args/**kwargs.
"""

import math
from typing import Dict

from exceptions import ValidationError

# Tuples: immutable configuration constants
CORE_SUBJECTS = ("python", "sql", "excel", "powerbi")
PROJECT_STATUSES = ("Not Started", "In Progress", "Submitted", "Approved")
MOCK_STATUSES = ("Not Scheduled", "Scheduled", "Cleared", "Failed")
DERIVED_SKILLS = (
    "PYTHON",
    "SQL",
    "EXCEL",
    "POWERBI",
    "CAPSTONE",
    "PROBLEM_SOLVING",
    "INTERVIEW_READY",
)
WEIGHTS = (
    ("attendance", 0.15),
    ("assessments", 0.35),
    ("project", 0.25),
    ("practice", 0.10),
    ("mock", 0.15),
)


def validate_score(score: float, label: str = "Score") -> float:
    """Validate that a score is a finite number between 0 and 100."""
    if isinstance(score, bool):
        raise ValidationError(f"{label} must be a number.")
    try:
        value = float(score)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} must be a number.") from exc
    if not math.isfinite(value) or value < 0 or value > 100:
        raise ValidationError(
            f"{label} must be a finite number between 0 and 100 (got {value})."
        )
    return round(value, 2)


def validate_single_line(text: str, label: str = "Field", allow_empty: bool = False) -> str:
    """Ensure text fields do not contain newline characters that break line-based TXT storage."""
    if not isinstance(text, str):
        raise ValidationError(f"{label} must be text.")
    if "\n" in text or "\r" in text:
        raise ValidationError(f"{label} cannot contain newline characters.")
    cleaned = text.strip()
    if not allow_empty and not cleaned:
        raise ValidationError(f"{label} cannot be empty.")
    return cleaned


def validate_identifier(identifier: str, label: str = "ID") -> str:
    """Validate IDs and disallow reserved storage delimiters."""
    cleaned = validate_single_line(identifier, label).upper()
    for ch in ("|", "~", ",", ":", "/"):
        if ch in cleaned:
            raise ValidationError(f"{label} cannot contain '{ch}'.")
    return cleaned


class Person:
    """Base class representing a person with encapsulated contact details."""

    def __init__(self, name: str, email: str, phone: str):
        self._name = ""
        self._email = ""
        self._phone = ""
        self.name = name
        self.email = email
        self.phone = phone

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        cleaned = validate_single_line(value, "Name")
        if len(cleaned) < 2:
            raise ValidationError("Name must be at least 2 characters long.")
        self._name = cleaned.title()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        cleaned = validate_single_line(value, "Email").lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValidationError(f"Invalid email address: '{value}'.")
        self._email = cleaned

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str) -> None:
        cleaned = validate_single_line(value, "Phone")
        digits = cleaned.replace("-", "").replace(" ", "")
        if not digits.isdigit() or len(digits) != 10:
            raise ValidationError("Phone number must contain exactly 10 digits.")
        self._phone = digits

    def get_summary(self) -> str:
        """Polymorphic method overridden by subclasses."""
        return f"{self._name} | {self._email} | {self._phone}"


class Student(Person):
    """Student model inheriting from Person and tracking all placement metrics."""

    def __init__(self, student_id: str, name: str, email: str, phone: str, batch_id: str):
        super().__init__(name, email, phone)
        self._student_id = validate_identifier(student_id, "Student ID")
        self._batch_id = validate_identifier(batch_id, "Batch ID")

        # Dictionaries for structured student progress
        self._attendance = {"attended": 0, "total": 0}
        self._python_parts = {"theory": 0.0, "coding": 0.0, "mcq": 0.0}
        self._scores = {subject: 0.0 for subject in CORE_SUBJECTS}
        self._project = {"title": "Not Assigned", "status": "Not Started", "score": 0.0}
        self._practice = {"sessions": 0, "problems_solved": 0}
        self._mock = {"status": "Not Scheduled", "tech": 0.0, "comm": 0.0}

        # Sets: derived skills reflect current thresholds; manual_skills hold custom tags
        self._derived_skills = set()
        self._manual_skills = set()

    @property
    def student_id(self) -> str:
        return self._student_id

    @property
    def batch_id(self) -> str:
        return self._batch_id

    @batch_id.setter
    def batch_id(self, value: str) -> None:
        self._batch_id = validate_identifier(value, "Batch ID")

    @property
    def attendance(self) -> dict:
        return dict(self._attendance)

    @property
    def attendance_pct(self) -> float:
        total = self._attendance["total"]
        return round((self._attendance["attended"] / total) * 100, 2) if total > 0 else 0.0

    @property
    def python_parts(self) -> dict:
        return dict(self._python_parts)

    @property
    def scores(self) -> dict:
        return dict(self._scores)

    @property
    def project(self) -> dict:
        return dict(self._project)

    @property
    def practice(self) -> dict:
        return dict(self._practice)

    @property
    def mock_interview(self) -> dict:
        return dict(self._mock)

    @property
    def skills(self) -> set:
        """Current verified skills (auto-derived from current results + custom skills)."""
        return self._derived_skills | self._manual_skills

    def _sync_derived_skills(self) -> None:
        """Recompute automatically derived skills so they always match current state."""
        derived = set()
        for subject in CORE_SUBJECTS:
            if self._scores.get(subject, 0.0) >= 60.0:
                derived.add(subject.upper())
        if self._project["status"] == "Approved":
            derived.add("CAPSTONE")
        if self._practice["problems_solved"] >= 50:
            derived.add("PROBLEM_SOLVING")
        if self._mock["status"] == "Cleared":
            derived.add("INTERVIEW_READY")
        self._derived_skills = derived

    def update_attendance(self, attended: int, total: int) -> None:
        if isinstance(attended, bool) or isinstance(total, bool):
            raise ValidationError("Attendance values must be integers.")
        if not isinstance(attended, int) or not isinstance(total, int):
            raise ValidationError("Attendance values must be integers.")
        if total <= 0 or attended < 0 or attended > total:
            raise ValidationError("Invalid attendance: 0 <= attended <= total and total > 0.")
        self._attendance["attended"] = attended
        self._attendance["total"] = total

    def update_python_score(self, theory: float, coding: float, mcq: float) -> float:
        t = validate_score(theory, "Python Theory")
        c = validate_score(coding, "Python Coding")
        m = validate_score(mcq, "Python MCQ")
        self._python_parts = {"theory": t, "coding": c, "mcq": m}
        # Weighted Python score: 30% Theory, 40% Coding, 30% MCQ
        composite = round(t * 0.30 + c * 0.40 + m * 0.30, 2)
        self._scores["python"] = composite
        self._sync_derived_skills()
        return composite

    def update_scores(self, *args: float, **kwargs: float) -> None:
        """Atomically validate all supplied core subject scores before updating."""
        if len(args) > len(CORE_SUBJECTS):
            raise ValidationError(
                f"At most {len(CORE_SUBJECTS)} positional scores allowed for {CORE_SUBJECTS}."
            )

        pending: Dict[str, float] = {}
        for subject, val in zip(CORE_SUBJECTS, args):
            pending[subject] = validate_score(val, subject.upper())

        for subject, val in kwargs.items():
            key = validate_single_line(subject, "Subject").lower()
            if key not in CORE_SUBJECTS:
                raise ValidationError(
                    f"Unknown subject '{subject}'. Allowed subjects: {CORE_SUBJECTS}."
                )
            if key in pending:
                raise ValidationError(f"Duplicate score supplied for subject '{key}'.")
            pending[key] = validate_score(val, key.upper())

        self._scores.update(pending)
        self._sync_derived_skills()

    def update_project(self, title: str, status: str, score: float = 0.0) -> None:
        clean_status = validate_single_line(status, "Project Status")
        if clean_status not in PROJECT_STATUSES:
            raise ValidationError(f"Project status must be one of {PROJECT_STATUSES}.")
        clean_title = validate_single_line(title, "Project Title", allow_empty=True) or "Capstone Project"
        clean_score = validate_score(score, "Project Score")
        self._project = {"title": clean_title, "status": clean_status, "score": clean_score}
        self._sync_derived_skills()

    def update_practice(self, sessions: int, problems_solved: int) -> None:
        if isinstance(sessions, bool) or isinstance(problems_solved, bool):
            raise ValidationError("Practice counts must be integers.")
        if not isinstance(sessions, int) or not isinstance(problems_solved, int):
            raise ValidationError("Practice counts must be integers.")
        if sessions < 0 or problems_solved < 0:
            raise ValidationError("Practice sessions and problems solved cannot be negative.")
        self._practice = {"sessions": sessions, "problems_solved": problems_solved}
        self._sync_derived_skills()

    def update_mock_interview(self, status: str, tech: float = 0.0, comm: float = 0.0) -> None:
        clean_status = validate_single_line(status, "Mock Status")
        if clean_status not in MOCK_STATUSES:
            raise ValidationError(f"Mock status must be one of {MOCK_STATUSES}.")
        t = validate_score(tech, "Mock Technical")
        c = validate_score(comm, "Mock Communication")
        self._mock = {"status": clean_status, "tech": t, "comm": c}
        self._sync_derived_skills()

    def add_skills(self, *skills: str) -> None:
        """Add custom (non-auto-derived) skill tags."""
        for skill in skills:
            cleaned = validate_single_line(skill, "Skill", allow_empty=True).upper()
            if not cleaned or cleaned in DERIVED_SKILLS:
                continue
            self._manual_skills.add(cleaned)

    def get_summary(self) -> str:
        """Override Person.get_summary() to show student-specific summary (Polymorphism)."""
        return f"[{self._student_id}] {self._name} (Batch: {self._batch_id}) | Att: {self.attendance_pct}%"


class Batch:
    """Represents a training batch with a set of enrolled student IDs."""

    def __init__(self, batch_id: str, name: str, track: str, instructor: str):
        self._batch_id = validate_identifier(batch_id, "Batch ID")
        self._name = validate_single_line(name, "Batch Name")
        self._track = validate_single_line(track, "Batch Track")
        self._instructor = validate_single_line(instructor, "Instructor").title()
        self._student_ids = set()

    @property
    def batch_id(self) -> str:
        return self._batch_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def track(self) -> str:
        return self._track

    @property
    def instructor(self) -> str:
        return self._instructor

    @property
    def student_ids(self) -> set:
        return set(self._student_ids)

    def add_student(self, student_id: str) -> None:
        self._student_ids.add(validate_identifier(student_id, "Student ID"))

    def remove_student(self, student_id: str) -> None:
        self._student_ids.discard(student_id.strip().upper())
