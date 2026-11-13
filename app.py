from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import sys
from pathlib import Path

import psycopg

from db import load_database_url

sys.path.insert(0, str(Path(__file__).resolve().parent / "model"))
from assignment_rules import SKILL_COLUMNS, assign_groups
from cluster_model import CENTROIDS

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
DATABASE_URL = load_database_url()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND), **kwargs)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/health":
            self._send_health()
            return
        if path == "/api/students":
            self._send_students()
            return
        if path == "/api/groups":
            self._send_groups()
            return
        super().do_GET()

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_health(self) -> None:
        try:
            with psycopg.connect(DATABASE_URL) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            self._send_json({"ok": True, "database": "connected"})
        except Exception:
            self._send_json({"ok": False, "database": "error"}, status=500)

    def _send_students(self) -> None:
        try:
            with psycopg.connect(DATABASE_URL) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT student_id, name FROM students ORDER BY student_id"
                    )
                    students = [
                        {"student_id": student_id, "name": name}
                        for student_id, name in cursor.fetchall()
                    ]
            self._send_json({"students": students})
        except Exception:
            self.send_error(500, "Could not read students from the database")

    def _send_groups(self) -> None:
        n_groups = 8
        try:
            with psycopg.connect(DATABASE_URL) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT netid, name,
                               skill_programming, skill_data_stats,
                               skill_frontend_design, skill_business_pitch
                        FROM students
                        ORDER BY netid
                        """
                    )
                    rows = cursor.fetchall()
        except Exception:
            self.send_error(500, "Could not read students from the database")
            return

        students = []
        name_by_id = {}
        for netid, name, skill_programming, skill_data_stats, skill_frontend_design, skill_business_pitch in rows:
            name_by_id[netid] = name
            students.append(
                {
                    "id": netid,
                    "skill_programming": skill_programming,
                    "skill_data_stats": skill_data_stats,
                    "skill_frontend_design": skill_frontend_design,
                    "skill_business_pitch": skill_business_pitch,
                }
            )

        assignments = assign_groups(students)
        class_clusters = sorted({student["cluster"] for student in assignments})

        groups = []
        groups_missing_a_cluster = 0
        for group_number in range(1, n_groups + 1):
            members = [student for student in assignments if student["group"] == group_number]
            cluster_counts = {
                str(cluster): sum(student["cluster"] == cluster for student in members)
                for cluster in class_clusters
            }
            if any(cluster_counts[str(cluster)] == 0 for cluster in class_clusters):
                groups_missing_a_cluster += 1
            groups.append(
                {
                    "group": group_number,
                    "members": sorted(name_by_id[student["id"]] for student in members),
                    "cluster_counts": cluster_counts,
                }
            )

        clusters = []
        for cluster_number, centroid in enumerate(CENTROIDS):
            clusters.append(
                {
                    "cluster": cluster_number,
                    "students": sum(
                        student["cluster"] == cluster_number for student in assignments
                    ),
                    "centroid": {
                        column: value
                        for column, value in zip(SKILL_COLUMNS, centroid)
                    },
                }
            )

        self._send_json(
            {
                "n_groups": n_groups,
                "groups": groups,
                "clusters": clusters,
                "groups_missing_a_cluster": groups_missing_a_cluster,
            }
        )

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving http://{HOST}:{PORT} from {FRONTEND}", flush=True)
    print("Student names loaded from Railway Postgres", flush=True)
    server.serve_forever()
