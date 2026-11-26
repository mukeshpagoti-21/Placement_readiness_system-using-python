# Project 25: Placement Readiness and Student Progress Management System

A clear, modular Python capstone application for training institutes to track student attendance, technical assessments, capstone projects, practice sessions, mock interviews, and campus placement readiness.

## Project Structure

```
project25_placement_readiness/
├── main.py          # Interactive 15-option CLI menu & isolated --demo runner
├── manager.py       # PlacementManager coordinating all 15 features
├── models.py        # Person, Student, Batch (OOP + collections + *args/**kwargs)
├── reports.py       # Polymorphic TXT reports & safe atomic TXT persistence
├── exceptions.py    # Custom exception hierarchy
├── test_project.py  # Automated unit tests
├── data/            # Live TXT records and exported TXT reports (app-relative)
└── demo_data/       # Isolated folder used by `python main.py --demo`
```

## Features Covered

1. Student Registration
2. Batch Management
3. Attendance Tracking
4. Python Assessment Scores (Theory, Coding, MCQ)
5. Manual SQL / Excel / Power BI Score Entry (`*args` & `**kwargs`)
6. Project Completion Status
7. Practice Session Tracking
8. Mock Interview Status
9. Performance Category (`Platinum`, `Gold`, `Silver`, `Bronze`)
10. Placement Eligibility Check
11. Student Search (by ID, name, batch, or category)
12. Top Performer Identification
13. Students Needing Improvement
14. Overall Progress Percentage (weighted score)
15. Simple TXT-Based Report Storage & Persistence

## Scoring Policy & Eligibility Rules

### 1. Overall Progress Weights (Total = 100%)

| Component | Weight | How Contribution (0–100) Is Calculated |
|---|---:|---|
| **Attendance** | **15%** | `(attended / total) * 100` (`0.0` if `total == 0`) |
| **Technical Assessments** | **35%** | Mean of `python`, `sql`, `excel`, `powerbi` (`python = 0.30*theory + 0.40*coding + 0.30*mcq`) |
| **Capstone Project** | **25%** | `Approved`: actual score (`0–100`, genuine `0` scores `0`); `Submitted`: `min(85, score)`; `In Progress`: `40`; `Not Started`: `0` |
| **Practice Sessions** | **10%** | `min(100, problems_solved)` (target benchmark: 100 problems) |
| **Mock Interview** | **15%** | `Cleared`: `(tech + comm) / 2`; `Scheduled`: `40`; `Failed`: `20`; `Not Scheduled`: `0` |

All assessment, project, and mock interview scores must be **finite numbers between 0 and 100** (`NaN` and `inf` are rejected). Bulk score updates via `record_subject_scores` / `update_scores` are **atomic**: all subject names and scores are validated before any change is applied, and unknown subject names are rejected.

### 2. Performance Categories

- **Platinum**: Overall progress >= `85%`, attendance >= `80%`, and project status == `Approved`
- **Gold**: Overall progress >= `75%` (without meeting all Platinum gates)
- **Silver**: Overall progress >= `60%`
- **Bronze**: Overall progress < `60%`

### 3. Placement Eligibility Thresholds

A student is **Placement Eligible (`True`)** only when **all 5** criteria are met:
1. **Attendance** >= `80%`
2. **Technical Assessment Average** >= `70%`
3. **Capstone Project Status** == `Approved`
4. **Mock Interview Status** == `Cleared`
5. **Practice Problems Solved** >= `50`

### 4. Verified Skill Labels

`student.skills` combines:
- **Auto-derived skills** (recalculated on every update so they always reflect current results):
  - `PYTHON`, `SQL`, `EXCEL`, `POWERBI` when that subject score >= `60`
  - `CAPSTONE` when project status == `Approved`
  - `PROBLEM_SOLVING` when `problems_solved` >= `50`
  - `INTERVIEW_READY` when mock interview status == `Cleared`
- **Custom skills** added via `add_skills(...)` for extra non-derived tags.

### 5. Safe TXT Storage & Demo Isolation

- Default storage resolves to `<app_dir>/data` regardless of current working directory.
- `save_all()` validates serialized data, writes `.tmp` files, verifies them on disk, keeps `.bak` copies of the previous valid dataset, and swaps atomically via `os.replace`.
- Delimiter characters (`%`, `|`, `~`, `,`, `\n`, `\r`) are escaped/unescaped safely on save/load, and newlines are rejected in single-line text fields.
- `python main.py --demo` runs inside `demo_data/` so live records in `data/` are never overwritten.

## How to Run

```powershell
python main.py          # Interactive CLI menu
python main.py --demo   # Run isolated sample demo (writes to demo_data/)
python test_project.py  # Run unit tests
```
