"""Assign students to groups by spreading skill clusters round-robin."""

import csv
from pathlib import Path

from cluster_model import predict_cluster

SKILL_COLUMNS = (
    "skill_programming",
    "skill_data_stats",
    "skill_frontend_design",
    "skill_business_pitch",
)


def assign_groups(students, n_groups=8):
    """Label each student with a cluster and a group number from 1 to n_groups.

    Clusters are dealt largest first. Within a cluster, students are ordered by
    id. Seats continue from group 1 through n_groups across that whole sequence.
    """
    labeled = []
    for student in students:
        skills = [float(student[column]) for column in SKILL_COLUMNS]
        labeled.append(
            {
                "id": student["id"],
                "cluster": predict_cluster(skills),
            }
        )

    by_cluster = {}
    for student in labeled:
        by_cluster.setdefault(student["cluster"], []).append(student)

    cluster_order = sorted(by_cluster, key=lambda cluster: (-len(by_cluster[cluster]), cluster))
    deal = []
    for cluster in cluster_order:
        members = sorted(by_cluster[cluster], key=lambda student: student["id"])
        deal.extend(members)

    group_by_id = {}
    for index, student in enumerate(deal):
        group_by_id[student["id"]] = (index % n_groups) + 1

    return [
        {
            "id": student["id"],
            "cluster": student["cluster"],
            "group": group_by_id[student["id"]],
        }
        for student in labeled
    ]


def load_students(path):
    with path.open(newline="", encoding="utf-8") as handle:
        students = []
        for row in csv.DictReader(handle):
            student = {"id": row["netid"]}
            for column in SKILL_COLUMNS:
                student[column] = float(row[column])
            students.append(student)
        return students


def main():
    assignments = assign_groups(load_students(Path(__file__).resolve().parent / "class_dataset.csv"))
    clusters = sorted({student["cluster"] for student in assignments})
    n_groups = max(student["group"] for student in assignments)
    missing = 0
    for group in range(1, n_groups + 1):
        members = [student for student in assignments if student["group"] == group]
        counts = {
            cluster: sum(student["cluster"] == cluster for student in members)
            for cluster in clusters
        }
        cluster_counts = ", ".join(f"cluster {cluster}: {counts[cluster]}" for cluster in clusters)
        print(f"group {group}: {len(members)} students ({cluster_counts})")
        if any(counts[cluster] == 0 for cluster in clusters):
            missing += 1
    print(f"groups missing a cluster: {missing}")


if __name__ == "__main__":
    main()
