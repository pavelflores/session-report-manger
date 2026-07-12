from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml

from app.models import Session, Student


class YamlRepository:
    def __init__(self, base_path: Path | str):
        self.base_path = Path(base_path)
        self.students_dir = self.base_path / "students"
        self.students_dir.mkdir(parents=True, exist_ok=True)

    def _student_dir(self, student_id: str) -> Path:
        return self.students_dir / student_id

    def _student_file(self, student_id: str) -> Path:
        return self._student_dir(student_id) / "student.yaml"

    def _session_dir(self, student_id: str) -> Path:
        return self._student_dir(student_id) / "sessions"

    def _session_file(self, student_id: str, folio: str) -> Path:
        return self._session_dir(student_id) / f"{folio}.yaml"

    def save_student(self, student: Student) -> Path:
        student_dir = self._student_dir(student.id)
        student_dir.mkdir(parents=True, exist_ok=True)
        payload = student.model_dump(mode="json")
        student_file = self._student_file(student.id)
        student_file.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return student_file

    def load_student(self, student_id: str) -> Optional[Student]:
        student_file = self._student_file(student_id)
        if not student_file.exists():
            return None
        payload = yaml.safe_load(student_file.read_text(encoding="utf-8")) or {}
        return Student.model_validate(payload)

    def list_students(self) -> List[Student]:
        students: List[Student] = []
        for student_dir in sorted(self.students_dir.iterdir()):
            if not student_dir.is_dir():
                continue
            student = self.load_student(student_dir.name)
            if student is not None:
                students.append(student)
        return students

    def save_session(self, student_id: str, session: Session) -> Path:
        session_dir = self._session_dir(student_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        payload = session.model_dump(mode="json")
        session_file = self._session_file(student_id, session.folio)
        session_file.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return session_file

    def list_sessions(self, student_id: str) -> List[Session]:
        session_dir = self._session_dir(student_id)
        if not session_dir.exists():
            return []
        sessions: List[Session] = []
        for session_file in sorted(session_dir.glob("*.yaml")):
            payload = yaml.safe_load(session_file.read_text(encoding="utf-8")) or {}
            sessions.append(Session.model_validate(payload))
        return sessions

    def next_folio(self, session_date):
        latest = 0
        for student in self.list_students():
            for session in self.list_sessions(student.id):
                if session.folio.startswith(f"SES-{session_date.strftime('%Y%m%d')}-"):
                    suffix = int(session.folio.split("-")[-1])
                    latest = max(latest, suffix)
        return f"SES-{session_date.strftime('%Y%m%d')}-{latest + 1:04d}"
