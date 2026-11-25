"""Domain models demonstrating OOP (Classes, Encapsulation, Inheritance, Polymorphism)
alongside Tuples, Sets, Dictionaries, Lists, Strings, and *args/**kwargs.
"""

from exceptions import ValidationError

# Tuples: immutable configuration constants
CORE_SUBJECTS = ("python", "sql", "excel", "powerbi")
PROJECT_STATUSES = ("Not Started", "In Progress", "Submitted", "Approved")
MOCK_STATUSES = ("Not Scheduled", "Scheduled", "Cleared", "Failed")
WEIGHTS = (
    ("attendance", 0.15),
    ("assessments", 0.35),
    ("project", 0.25),
    ("practice", 0.10),
    ("mock", 0.15),
)


def validate_score(score: float, label: str = "Score") -> float:
    """Validate that a numeric score falls between 0 and 100."""
    try:
        value = float(score)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} must be a number.") from exc
    if value < 0 or value > 100:
        raise ValidationError(f"{label} must be between 0 and 100 (got {value}).")
    return round(value, 2)


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
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValidationError("Name must be at least 2 characters long.")
        self._name = cleaned.title()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        cleaned = value.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValidationError(f"Invalid email address: '{value}'.")
        self._email = cleaned

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str) -> None:
        digits = value.strip().replace("-", "").replace(" ", "")
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
        clean_id = student_id.strip().upper()
        if not clean_id:
            raise ValidationError("Student ID cannot be empty.")

        self._student_id = clean_id
        self._batch_id = batch_id.strip().upper()

        # Dictionaries for structured student progress
        self._attendance = {"attended": 0, "total": 0}
        self._python_parts = {"theory": 0.0, "coding": 0.0, "mcq": 0.0}
        self._scores = {subject: 0.0 for subject in CORE_SUBJECTS}
        self._project = {"title": "Not Assigned", "status": "Not Started", "score": 0.0}
        self._practice = {"sessions": 0, "problems_solved": 0}
        self._mock = {"status": "Not Scheduled", "tech": 0.0, "comm": 0.0}

        # Set of verified technical skills
        self._skills = set()

    @property
    def student_id(self) -> str:
        return self._student_id

    @property
    def batch_id(self) -> str:
        return self._batch_id

    @batch_id.setter
    def batch_id(self, value: str) -> None:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValidationError("Batch ID cannot be empty.")
        self._batch_id = cleaned

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
        return set(self._skills)

    def update_attendance(self, attended: int, total: int) -> None:
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
        if composite >= 60:
            self._skills.add("PYTHON")
        return composite

    def update_scores(self, *args: float, **kwargs: float) -> None:
        """Update subject scores dynamically using *args and **kwargs."""
        for subject, val in zip(CORE_SUBJECTS, args):
            self._set_subject_score(subject, val)
        for subject, val in kwargs.items():
            self._set_subject_score(subject, val)

    def _set_subject_score(self, subject: str, val: float) -> None:
        key = subject.strip().lower()
        clean_val = validate_score(val, key.upper())
        self._scores[key] = clean_val
        if clean_val >= 60:
            self._skills.add(key.upper())

    def update_project(self, title: str, status: str, score: float = 0.0) -> None:
        if status not in PROJECT_STATUSES:
            raise ValidationError(f"Project status must be one of {PROJECT_STATUSES}.")
        clean_title = title.strip() or "Capstone Project"
        clean_score = validate_score(score, "Project Score")
        self._project = {"title": clean_title, "status": status, "score": clean_score}
        if status == "Approved":
            self._skills.add("CAPSTONE")

    def update_practice(self, sessions: int, problems_solved: int) -> None:
        if sessions < 0 or problems_solved < 0:
            raise ValidationError("Practice sessions and problems solved cannot be negative.")
        self._practice = {"sessions": sessions, "problems_solved": problems_solved}
        if problems_solved >= 50:
            self._skills.add("PROBLEM_SOLVING")

    def update_mock_interview(self, status: str, tech: float = 0.0, comm: float = 0.0) -> None:
        if status not in MOCK_STATUSES:
            raise ValidationError(f"Mock status must be one of {MOCK_STATUSES}.")
        t = validate_score(tech, "Mock Technical")
        c = validate_score(comm, "Mock Communication")
        self._mock = {"status": status, "tech": t, "comm": c}
        if status == "Cleared":
            self._skills.add("INTERVIEW_READY")

    def add_skills(self, *skills: str) -> None:
        for skill in skills:
            if skill.strip():
                self._skills.add(skill.strip().upper())

    def get_summary(self) -> str:
        """Override Person.get_summary() to show student-specific summary (Polymorphism)."""
        return f"[{self._student_id}] {self._name} (Batch: {self._batch_id}) | Att: {self.attendance_pct}%"


class Batch:
    """Represents a training batch with a set of enrolled student IDs."""

    def __init__(self, batch_id: str, name: str, track: str, instructor: str):
        clean_id = batch_id.strip().upper()
        if not clean_id or not name.strip():
            raise ValidationError("Batch ID and name cannot be empty.")
        self._batch_id = clean_id
        self._name = name.strip()
        self._track = track.strip()
        self._instructor = instructor.strip().title()
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
        self._student_ids.add(student_id.strip().upper())

    def remove_student(self, student_id: str) -> None:
        self._student_ids.discard(student_id.strip().upper())
