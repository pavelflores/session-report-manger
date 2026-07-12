from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import os

from typing import Optional

from jinja2 import Environment, FileSystemLoader

from app.models import Session, Student
from app.storage import YamlRepository


class StudentService:
    def __init__(self, repository: YamlRepository):
        self.repository = repository

    def create_student(self, **data) -> Student:
        student_id = self._build_student_id(data.get("name", "student"))
        student = Student(id=student_id, **data)
        self.repository.save_student(student)
        return student

    def list_students(self) -> list[Student]:
        return self.repository.list_students()

    def get_student(self, student_id: str) -> Optional[Student]:
        return self.repository.load_student(student_id)

    def _build_student_id(self, name: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "", name.lower()).strip() or "student"
        candidate = base
        suffix = 1
        while self.repository.load_student(candidate) is not None:
            candidate = f"{base}{suffix}"
            suffix += 1
        return candidate


class SessionService:
    def __init__(self, repository: YamlRepository, report_service: Optional["ReportService"] = None):
        self.repository = repository
        self.report_service = report_service

    def create_session(
        self,
        student: Student,
        *,
        duration_hours: float,
        summary: str,
        next_session: str,
        date: Optional[datetime] = None,
    ) -> Session:
        session_date = date or datetime.now()
        folio = self.repository.next_folio(session_date)
        existing_sessions = self.repository.list_sessions(student.id)
        session_number = len(existing_sessions) + 1
        total_amount = round(student.hourly_rate * duration_hours, 2)
        session = Session(
            id=f"{student.id}-{folio}",
            student_id=student.id,
            date=session_date,
            duration_hours=duration_hours,
            summary=summary,
            next_session=next_session,
            total_amount=total_amount,
            folio=folio,
            session_number=session_number,
        )
        self.repository.save_session(student.id, session)
        if self.report_service is not None:
            report_path = self.report_service.generate_report(student, session)
            session.report_path = report_path
            self.repository.save_session(student.id, session)
        return session


class ReportService:
    def __init__(self, template_dir: Path | str):
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)), autoescape=True)

    def render_report_html(self, student: Student, session: Session) -> str:
        template = self.env.get_template("report.html")
        return template.render(student=student, session=session)

    def generate_report(self, student: Student, session: Session) -> str:
        report_dir = Path(__file__).resolve().parents[1] / "data" / "students" / student.id / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{session.folio}.pdf"

        for old_report in report_dir.glob("*.html"):
            if old_report.name.startswith(session.folio):
                old_report.unlink(missing_ok=True)

        html_content = self.render_report_html(student, session)
        try:
            from weasyprint import HTML

            HTML(string=html_content).write_pdf(report_path)
        except Exception as exc:
            fallback_path = report_dir / f"{session.folio}.html"
            fallback_path.write_text(html_content, encoding="utf-8")
            print(f"WeasyPrint failed: {exc}")
            return str(fallback_path)

        return str(report_path)


class EmailService:
    def __init__(self, sender_email: str, sender_password: str):
        self.sender_email = sender_email
        self.sender_password = sender_password

    def send_report_email(self, recipient_email: str, recipient_name: str, session: Session, student: Student, pdf_path: str) -> bool:
        """Envía el reporte en PDF por correo adjunto."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = recipient_email
            msg["Subject"] = f"Reporte de sesión - {session.folio}"

            body = f"""Hola {recipient_name},

Te adjuntamos el reporte de la sesión de {student.name} del {session.date.strftime('%d/%m/%Y')}.

Detalles:
- Duración: {session.duration_hours} horas
- Total: ${session.total_amount:.2f}
- Folio: {session.folio}
- Próxima sesión: {session.next_session}

Cualquier duda, no dudes en comunicarte.

Saludos,
Psi. Yajaira Elizabeth Flores Horta
Cédula: 1482036
Celular: 33 3019 4548
"""

            msg.attach(MIMEText(body, "plain"))

            if Path(pdf_path).exists():
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename= {Path(pdf_path).name}")
                    msg.attach(part)

            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as exc:
            print(f"Error al enviar correo: {exc}")
            return False
