"""Main entry point: Interactive CLI menu and automated --demo mode."""

import sys

from exceptions import PlacementError
from manager import PlacementManager


def seed_sample_data(manager: PlacementManager) -> None:
    """Populate realistic sample batches and students for demo/testing."""
    if manager.batches:
        return

    manager.create_batch("B01", "Data Analytics Cohort", "Data Analytics", "Meera Nair")
    manager.create_batch("B02", "Python Full Stack", "Full Stack", "Arjun Kulkarni")

    # Top performer (Platinum, Eligible)
    manager.register_student("STU101", "Aditi Sharma", "aditi@example.com", "9876543210", "B01")
    manager.record_attendance("STU101", 46, 50)
    manager.record_python_score("STU101", 90, 95, 88)
    manager.record_subject_scores("STU101", sql=92, excel=88, powerbi=91)
    manager.record_project("STU101", "Sales Forecasting Dashboard", "Approved", 94)
    manager.record_practice("STU101", 25, 110)
    manager.record_mock_interview("STU101", "Cleared", tech=90, comm=88)

    # Solid performer (Gold, Eligible)
    manager.register_student("STU102", "Rohan Verma", "rohan@example.com", "9876543211", "B01")
    manager.record_attendance("STU102", 42, 50)
    manager.record_python_score("STU102", 80, 82, 78)
    manager.record_subject_scores("STU102", sql=84, excel=79, powerbi=81)
    manager.record_project("STU102", "Customer Churn Analysis", "Approved", 82)
    manager.record_practice("STU102", 18, 70)
    manager.record_mock_interview("STU102", "Cleared", tech=78, comm=76)

    # Student needing improvement (Bronze, Not Eligible)
    manager.register_student("STU103", "Deepak Joshi", "deepak@example.com", "9876543212", "B02")
    manager.record_attendance("STU103", 32, 50)
    manager.record_python_score("STU103", 52, 48, 55)
    manager.record_subject_scores("STU103", sql=45, excel=58, powerbi=50)
    manager.record_project("STU103", "Inventory Tracker", "In Progress", 40)
    manager.record_practice("STU103", 6, 22)
    manager.record_mock_interview("STU103", "Failed", tech=42, comm=50)


def run_demo() -> None:
    """Run a concise demonstration of all 15 features."""
    manager = PlacementManager()
    seed_sample_data(manager)

    print("\n=== PLACEMENT READINESS SYSTEM DEMO ===")
    print(f"Batches : {list(manager.batches.keys())}")
    print(f"Students: {len(manager.students)}")

    print("\n-- Top Performers --")
    for rank, (student, score, category) in enumerate(manager.get_top_performers(3), start=1):
        eligible, _ = manager.check_placement_eligibility(student)
        print(f"  #{rank} {student.get_summary()} | Progress: {score}% | {category} | Eligible: {eligible}")

    print("\n-- Students Needing Improvement --")
    for student, score, reasons in manager.get_students_needing_improvement():
        print(f"  {student.student_id} ({student.name}) - {score}% -> {', '.join(reasons)}")

    print("\n-- Search Example (query='Aditi') --")
    for s in manager.search_students("Aditi", by="name"):
        print(f"  Found: {s.get_summary()}")

    print("\n-- Batch B01 Skills (Set Operations) --")
    skills = manager.analyze_batch_skills("B01")
    print(f"  All Skills   : {sorted(skills['all_skills'])}")
    print(f"  Common Skills: {sorted(skills['common_skills'])}")

    manager.save_data()
    p1 = manager.export_student_report("STU101")
    p2 = manager.export_summary_report()
    print(f"\nSaved TXT data & reports:\n  - {p1}\n  - {p2}")


def run_cli() -> None:
    """Interactive menu loop."""
    manager = PlacementManager()
    manager.load_data()
    if not manager.batches and not manager.students:
        seed_sample_data(manager)

    menu = """
--- Placement Readiness Menu ---
1. Create Batch                9.  Update Mock Interview
2. Register Student            10. View Student Progress & Eligibility
3. Record Attendance           11. Search Students
4. Record Python Scores        12. Top Performers
5. Record SQL/Excel/PowerBI    13. Students Needing Improvement
6. Update Project Status       14. Export TXT Reports
7. Update Practice Sessions    15. Save & Exit
8. List All Batches & Students
"""
    while True:
        print(menu)
        choice = input("Choose an option (1-15): ").strip()
        try:
            if choice == "1":
                bid = input("Batch ID: ")
                name = input("Batch Name: ")
                track = input("Track: ")
                inst = input("Instructor: ")
                manager.create_batch(bid, name, track, inst)
                print("Batch created.")
            elif choice == "2":
                sid = input("Student ID: ")
                name = input("Name: ")
                email = input("Email: ")
                phone = input("Phone (10 digits): ")
                bid = input("Batch ID: ")
                manager.register_student(sid, name, email, phone, bid)
                print("Student registered.")
            elif choice == "3":
                sid = input("Student ID: ")
                att = int(input("Attended sessions: "))
                tot = int(input("Total sessions: "))
                pct = manager.record_attendance(sid, att, tot)
                print(f"Attendance updated: {pct}%")
            elif choice == "4":
                sid = input("Student ID: ")
                t = float(input("Theory (0-100): "))
                c = float(input("Coding (0-100): "))
                m = float(input("MCQ (0-100): "))
                score = manager.record_python_score(sid, t, c, m)
                print(f"Python composite score: {score}%")
            elif choice == "5":
                sid = input("Student ID: ")
                sql = float(input("SQL score: "))
                excel = float(input("Excel score: "))
                pbi = float(input("Power BI score: "))
                scores = manager.record_subject_scores(sid, sql=sql, excel=excel, powerbi=pbi)
                print(f"Updated scores: {scores}")
            elif choice == "6":
                sid = input("Student ID: ")
                title = input("Project Title: ")
                status = input("Status (Not Started/In Progress/Submitted/Approved): ")
                score = float(input("Score (0-100): "))
                manager.record_project(sid, title, status, score)
                print("Project updated.")
            elif choice == "7":
                sid = input("Student ID: ")
                sess = int(input("Sessions count: "))
                probs = int(input("Problems solved: "))
                manager.record_practice(sid, sess, probs)
                print("Practice updated.")
            elif choice == "8":
                for b in manager.batches.values():
                    print(f"Batch {b.batch_id}: {b.name} ({b.track}) - {len(b.student_ids)} students")
                for s in manager.students.values():
                    print(" ", s.get_summary())
            elif choice == "9":
                sid = input("Student ID: ")
                status = input("Status (Not Scheduled/Scheduled/Cleared/Failed): ")
                tech = float(input("Tech rating (0-100): "))
                comm = float(input("Comm rating (0-100): "))
                manager.record_mock_interview(sid, status, tech, comm)
                print("Mock interview updated.")
            elif choice == "10":
                sid = input("Student ID: ")
                s = manager.get_student(sid)
                prog = manager.calculate_overall_progress(s)
                cat = manager.get_performance_category(s)
                ok, reasons = manager.check_placement_eligibility(s)
                print(f"{s.get_summary()} | Progress: {prog}% | Category: {cat} | Eligible: {ok}")
                for r in reasons:
                    print(f"  - {r}")
            elif choice == "11":
                by = input("Search by (name/id/batch/category): ")
                query = input("Search query: ")
                results = manager.search_students(query, by=by)
                print(f"Found {len(results)} student(s):")
                for s in results:
                    print(" ", s.get_summary())
            elif choice == "12":
                n = int(input("How many top performers? "))
                for idx, (s, sc, cat) in enumerate(manager.get_top_performers(n), start=1):
                    print(f"#{idx} {s.student_id} {s.name} - {sc}% ({cat})")
            elif choice == "13":
                flagged = manager.get_students_needing_improvement()
                for s, sc, reasons in flagged:
                    print(f"{s.student_id} {s.name} ({sc}%): {', '.join(reasons)}")
            elif choice == "14":
                path = manager.export_summary_report()
                print(f"Summary report exported to {path}")
            elif choice == "15":
                manager.save_data()
                print("Data saved to TXT files. Goodbye!")
                break
            else:
                print("Invalid option. Choose 1-15.")
        except (PlacementError, ValueError) as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_demo()
    else:
        run_cli()
