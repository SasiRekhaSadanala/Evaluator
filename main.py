"""
Main entry point for evaluation orchestrator.
Demonstrates a complete workflow: load rubric, read submissions, evaluate, report results.
"""

from controller.orchestrator import Orchestrator
from utils.rubric import Rubric
from utils.csv_export import export_results_to_csv, export_results_to_detailed_csv


def main():
    """Run a complete evaluation workflow."""

    # ============================================================================
    # SETUP
    # ============================================================================

    print("=" * 80)
    print("EVALUATION ORCHESTRATOR - DEMO RUN")
    print("=" * 80)
    print()

    # Initialize rubric with defaults
    print("[1] Loading rubric...")
    rubric = Rubric()  # Uses default rubric
    print(f"    ✓ Rubric loaded: {rubric.rubric.get('name', 'Unknown')}")
    print(f"    - Code weight: {rubric.get_weight('code')} (max score: {rubric.get_max_score('code')})")
    print(f"    - Content weight: {rubric.get_weight('content')} (max score: {rubric.get_max_score('content')})")
    print()

    # ============================================================================
    # CONFIGURATION
    # ============================================================================

    # Hardcoded paths and assignment config
    ASSIGNMENT_TYPE = "code"  # Change to 'code', 'content', or 'mixed'
    SUBMISSIONS_FOLDER = "./sample_data/submissions"  # Update with actual folder path
    
    # Read problem statement
    with open("./sample_data/problem.txt", "r") as f:
        PROBLEM_STATEMENT = f.read()
    
    IDEAL_REFERENCE = """
    A good solution demonstrates:
    1. Clear problem understanding: identifies even numbers
    2. Proper error handling: handles empty or invalid inputs
    3. Efficient iteration: uses appropriate loops
    4. Clean code: meaningful variable names and comments
    5. Testing: shows awareness of test cases
    """

    print(f"[2] Configuration:")
    print(f"    - Assignment Type: {ASSIGNMENT_TYPE}")
    print(f"    - Submissions Folder: {SUBMISSIONS_FOLDER}")
    print(f"    - Problem Statement: {PROBLEM_STATEMENT[:60]}...")
    print()

    # ============================================================================
    # EVALUATE
    # ============================================================================

    print("[3] Initializing orchestrator...")
    orchestrator = Orchestrator(rubric=rubric)
    print("    ✓ Orchestrator ready")
    print()

    print("[4] Evaluating submissions...")
    try:
        results = orchestrator.evaluate_submissions(
            assignment_type=ASSIGNMENT_TYPE,
            folder_path=SUBMISSIONS_FOLDER,
            problem_statement=PROBLEM_STATEMENT,
            ideal_reference=IDEAL_REFERENCE,
        )
        print(f"    ✓ Evaluated {len(results)} student submission(s)")
    except FileNotFoundError as e:
        print(f"    ✗ Error: {e}")
        print(f"    → Make sure '{SUBMISSIONS_FOLDER}' exists with student submissions")
        return
    except Exception as e:
        print(f"    ✗ Unexpected error: {e}")
        return

    print()

    # ============================================================================
    # REPORT RESULTS
    # ============================================================================

    print("=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80)
    print()

    if not results:
        print("No results to display.")
        return

    for student_name, evaluation in results.items():
        print(f"Student: {student_name}")
        print(f"  File: {evaluation.get('file', 'N/A')}")
        print(f"  Assignment Type: {evaluation.get('assignment_type', 'N/A')}")
        print(f"  Score: {evaluation.get('final_score', 'N/A')} / {evaluation.get('max_score', 100)}")
        print()

        # Print feedback
        feedback = evaluation.get("combined_feedback", [])
        if feedback:
            print("  Feedback:")
            for item in feedback:
                # Format: indent feedback items, handle section headers
                if item.startswith("##"):
                    print(f"    {item}")
                else:
                    print(f"      {item}")
            print()

        print("-" * 80)
        print()

    # ============================================================================
    # SUMMARY
    # ============================================================================

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total_students = len(results)
    scores = [r.get("final_score", 0) for r in results.values()]
    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0

    print(f"  Total Students: {total_students}")
    print(f"  Average Score: {avg_score:.2f} / 100")
    print(f"  Highest Score: {max_score:.2f} / 100")
    print(f"  Lowest Score: {min_score:.2f} / 100")
    print()

    # ============================================================================
    # EXPORT RESULTS
    # ============================================================================

    print("[5] Exporting results to CSV...")
    try:
        csv_path = export_results_to_csv(results)
        print(f"    ✓ Results exported to: {csv_path}")

        detailed_csv_path = export_results_to_detailed_csv(results)
        print(f"    ✓ Detailed results exported to: {detailed_csv_path}")
    except Exception as e:
        print(f"    ✗ Error exporting results: {e}")

    print()
    print("✓ Evaluation complete!")


if __name__ == "__main__":
    main()
