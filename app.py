from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path

import psycopg

from db import load_database_url

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

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving http://{HOST}:{PORT} from {FRONTEND}", flush=True)
    print("Student names loaded from Railway Postgres", flush=True)
    server.serve_forever()
