# Project 25: Placement Readiness and Student Progress Management System

A clear, modular Python capstone application for training institutes to track student attendance, technical assessments, capstone projects, practice sessions, mock interviews, and campus placement readiness.

## Project Structure

```
project25_placement_readiness/
├── main.py          # Interactive 15-option CLI menu & --demo runner
├── manager.py       # PlacementManager coordinating all 15 features
├── models.py        # Person, Student, Batch (OOP + collections + *args/**kwargs)
├── reports.py       # Polymorphic TXT reports & pipe-delimited TXT persistence
├── exceptions.py    # Custom exception hierarchy
├── test_project.py  # Automated unit tests
└── data/            # Saved TXT records and exported TXT reports
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

## How to Run

```powershell
python main.py          # Interactive CLI menu
python main.py --demo   # Run automated sample demo
python test_project.py  # Run unit tests
```
