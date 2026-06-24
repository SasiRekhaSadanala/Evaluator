"""
Seed realistic student submission data into PostgreSQL.

Run: python -m backend.seed_data
"""

import random
from datetime import datetime, timedelta, timezone

from backend.core.services.database import get_db, init_db


STUDENTS = [
    "c1_Result",
    "c2_Result",
    "Two_sum_Result",
    "student1_good_Result",
    "alice_johnson_Result",
    "bob_kumar_Result",
    "sara_malik_Result",
    "omar_sheikh_Result",
]

TOPICS = [
    "Sorting Algorithms",
    "Data Structures",
    "Dynamic Programming",
    "Graph Theory",
    "Recursion",
    "OOP Concepts",
    "String Manipulation",
]

ASSIGNMENTS = [
    ("hw1_bubble_sort", "Sorting Algorithms"),
    ("hw2_linked_list", "Data Structures"),
    ("hw3_fibonacci", "Dynamic Programming"),
    ("hw4_bfs_dfs", "Graph Theory"),
    ("hw5_factorial", "Recursion"),
    ("hw6_classes", "OOP Concepts"),
    ("hw7_palindrome", "String Manipulation"),
    ("hw8_merge_sort", "Sorting Algorithms"),
    ("hw9_binary_tree", "Data Structures"),
    ("hw10_knapsack", "Dynamic Programming"),
    ("hw11_dijkstra", "Graph Theory"),
    ("hw12_tower_hanoi", "Recursion"),
]

# Student archetypes — base skill + growth rate
STUDENT_PROFILES = {
    "c1_Result":              {"base": 45, "growth": 2.5, "variance": 8},
    "c2_Result":              {"base": 55, "growth": 1.5, "variance": 10},
    "Two_sum_Result":         {"base": 70, "growth": 1.0, "variance": 6},
    "student1_good_Result":   {"base": 85, "growth": 0.8, "variance": 4},
    "alice_johnson_Result":   {"base": 78, "growth": 1.2, "variance": 5},
    "bob_kumar_Result":       {"base": 60, "growth": 2.0, "variance": 7},
    "sara_malik_Result":      {"base": 90, "growth": 0.3, "variance": 3},
    "omar_sheikh_Result":     {"base": 65, "growth": 1.8, "variance": 9},
}


def generate_scores():
    """Generate realistic score progressions for all students."""
    records = []
    now = datetime.now(timezone.utc)

    for student_id in STUDENTS:
        profile = STUDENT_PROFILES[student_id]
        base = profile["base"]
        growth = profile["growth"]
        variance = profile["variance"]

        for i, (assignment_id, topic_tag) in enumerate(ASSIGNMENTS):
            # Score improves over time with some noise
            raw_score = base + (growth * i) + random.gauss(0, variance)
            score = max(5.0, min(100.0, round(raw_score, 1)))

            # Spread submissions over the last 30 days
            days_ago = len(ASSIGNMENTS) - i
            submitted_at = now - timedelta(
                days=days_ago,
                hours=random.randint(0, 12),
                minutes=random.randint(0, 59),
            )

            records.append({
                "student_id": student_id,
                "assignment_id": assignment_id,
                "topic_tag": topic_tag,
                "score": score,
                "submitted_at": submitted_at,
            })

    return records


def seed():
    """Insert seed data into PostgreSQL."""
    init_db()
    db = get_db()

    if not db.available:
        print("✗ PostgreSQL is not available. Cannot seed data.")
        return

    # Clear existing data first
    db.execute("DELETE FROM student_scores;")
    print("✓ Cleared existing student_scores data.")

    records = generate_scores()

    for r in records:
        db.execute(
            """
            INSERT INTO student_scores (student_id, assignment_id, topic_tag, score, submitted_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [r["student_id"], r["assignment_id"], r["topic_tag"], r["score"], r["submitted_at"]],
        )

    print(f"✓ Inserted {len(records)} score records for {len(STUDENTS)} students.")
    print(f"  Topics: {len(TOPICS)}")
    print(f"  Assignments: {len(ASSIGNMENTS)}")

    # Print a quick summary
    for student_id in STUDENTS:
        row = db.execute_one(
            "SELECT COUNT(*) as cnt, ROUND(AVG(score)::numeric, 1) as avg FROM student_scores WHERE student_id = %s",
            [student_id],
        )
        print(f"  → {student_id}: {row['cnt']} submissions, avg {row['avg']}")


if __name__ == "__main__":
    seed()
