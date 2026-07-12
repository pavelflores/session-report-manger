from __future__ import annotations

from datetime import datetime
from pathlib import Path
import urllib.parse
import os

import streamlit as st

from app.services import ReportService, SessionService, StudentService, EmailService
from app.storage import YamlRepository

BASE_DIR = Path(__file__).resolve().parents[1]
REPO = YamlRepository(BASE_DIR / "data")
REPORT_SERVICE = ReportService(BASE_DIR / "templates")
STUDENT_SERVICE = StudentService(REPO)
SESSION_SERVICE = SessionService(REPO, REPORT_SERVICE)

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "994elizaflores.14@gmail.com")
SENDER_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
EMAIL_SERVICE = EmailService(SENDER_EMAIL, SENDER_PASSWORD) if SENDER_PASSWORD else None


def generate_whatsapp_link(phone: str, message: str) -> str:
    """Genera un link de WhatsApp con el mensaje."""
    if not phone:
        return ""
    phone_clean = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not phone_clean.startswith("52"):
        phone_clean = f"52{phone_clean}"
    message_encoded = urllib.parse.quote(message)
    return f"https://wa.me/{phone_clean}?text={message_encoded}"


def generate_mailto_link(email: str, subject: str, body: str) -> str:
    """Genera un link mailto con asunto y cuerpo."""
    if not email:
        return ""
    subject_encoded = urllib.parse.quote(subject)
    body_encoded = urllib.parse.quote(body)
    return f"mailto:{email}?subject={subject_encoded}&body={body_encoded}"

st.set_page_config(page_title="Session Report Manager", page_icon="📄", layout="wide")

st.title("📋 Session Report Manager")
st.caption("Sistema de gestión de sesiones, alumnos y reportes PDF profesionales")

if "students" not in st.session_state:
    st.session_state.students = STUDENT_SERVICE.list_students()

with st.sidebar:
    st.header("Registrar alumno")
    with st.form("student_form"):
        student_name = st.text_input("Nombre del alumno")
        parent_name = st.text_input("Nombre del padre/madre")
        email = st.text_input("Correo")
        whatsapp = st.text_input("WhatsApp")
        hourly_rate = st.number_input("Costo por hora", min_value=0.0, step=1.0)
        service_type = st.text_input("Tipo de servicio", value="clase particular")
        submitted = st.form_submit_button("Guardar alumno")
        if submitted and student_name:
            student = STUDENT_SERVICE.create_student(
                name=student_name,
                parent_name=parent_name,
                email=email,
                whatsapp=whatsapp,
                hourly_rate=hourly_rate,
                service_type=service_type,
            )
            st.session_state.students = STUDENT_SERVICE.list_students()
            st.success(f"Alumno registrado: {student.name} ({student.id})")

st.header("Alumnos")
if not st.session_state.students:
    st.info("Aún no hay alumnos registrados.")
else:
    student_options = {student.name: student.id for student in st.session_state.students}
    selected_name = st.selectbox("Selecciona un alumno", list(student_options.keys()))
    selected_student = next(student for student in st.session_state.students if student.id == student_options[selected_name])

    st.subheader(f"Sesiones de {selected_student.name}")
    sessions = REPO.list_sessions(selected_student.id)
    if sessions:
        for session in sorted(sessions, key=lambda item: item.date, reverse=True):
            with st.expander(f"{session.folio} - {session.date.strftime('%d/%m/%Y')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Duración:** {session.duration_hours} horas")
                    st.write(f"**Total:** ${session.total_amount}")
                with col2:
                    st.write(f"**Número de sesión:** {session.session_number}")
                    if session.report_path:
                        st.write(f"✅ **Reporte generado**")
                
                
                st.divider()
                st.write(f"**Resumen:** {session.summary}")
                st.write(f"**Próxima sesión:** {session.next_session}")
                
                st.divider()
                st.subheader("📤 Acciones")
                col_download, col_whatsapp, col_email = st.columns(3)
                
                with col_download:
                    if session.report_path and Path(session.report_path).exists():
                        with open(session.report_path, "rb") as pdf_file:
                            st.download_button(
                                label="⬇️ Descargar PDF",
                                data=pdf_file.read(),
                                file_name=f"{session.folio}.pdf",
                                mime="application/pdf",
                                key=f"download_{session.folio}"
                            )
                
                with col_whatsapp:
                    if selected_student.whatsapp:
                        whatsapp_msg = f"Hola {selected_student.parent_name or 'Padre/Madre'}!\n\nTe compartimos el reporte de la sesión del {session.date.strftime('%d/%m/%Y')}.\n\nDuración: {session.duration_hours} horas\nTotal: ${session.total_amount}\n\nFolio: {session.folio}"
                        whatsapp_link = generate_whatsapp_link(selected_student.whatsapp, whatsapp_msg)
                        st.markdown(f"[📱 Enviar WhatsApp]({whatsapp_link})")
                
                with col_email:
                    if selected_student.email:
                        if st.button("✉️ Enviar Correo", key=f"email_{session.folio}"):
                            if EMAIL_SERVICE and session.report_path:
                                with st.spinner("📨 Enviando correo..."):
                                    success = EMAIL_SERVICE.send_report_email(
                                        recipient_email=selected_student.email,
                                        recipient_name=selected_student.parent_name or "Padre/Madre",
                                        session=session,
                                        student=selected_student,
                                        pdf_path=session.report_path
                                    )
                                    if success:
                                        st.success(f"✅ Correo enviado a {selected_student.email}")
                                    else:
                                        st.error("❌ Error al enviar el correo")
                            else:
                                st.error("⚠️ No hay PDF o credenciales configuradas")
    else:
        st.info("No hay sesiones registradas para este alumno.")

    st.divider()
    st.subheader("Registrar sesión")
    with st.form("session_form"):
        date = st.date_input("Fecha")
        duration_hours = st.number_input("Duración (horas)", min_value=0.5, step=0.5)
        summary = st.text_area("Resumen de la sesión")
        next_session = st.text_area("Próxima sesión")
        submitted = st.form_submit_button("Guardar sesión")
        if submitted:
            session = SESSION_SERVICE.create_session(
                selected_student,
                duration_hours=duration_hours,
                summary=summary,
                next_session=next_session,
                date=datetime(date.year, date.month, date.day),
            )
            st.success(f"✅ **Sesión guardada exitosamente!**")
            st.info(f"""
            📋 **Detalles de la sesión:**
            - **Folio:** {session.folio}
            - **Alumno:** {selected_student.name}
            - **Fecha:** {session.date.strftime('%d/%m/%Y')}
            - **Duración:** {session.duration_hours} horas
            - **Total:** ${session.total_amount}
            - **PDF:** ✅ Generado
            
            Puedes enviar el reporte al padre/madre desde la sección de sesiones.
            """)
            st.rerun()
