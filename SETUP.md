# Configuración de desarrollo

## Variables de entorno

Crea un archivo `.env` en la raíz del proyecto (no lo subas a git):

```bash
cp .env.example .env
```

Luego edita `.env` y añade:
- `GMAIL_APP_PASSWORD`: Contraseña de aplicación de Gmail (obtenerla de https://myaccount.google.com/apppasswords)
- `SENDER_EMAIL`: Email desde el que enviar correos (ej: 994elizaflores.14@gmail.com)

## Instalación

### Paso 1: Instalar dependencias del sistema (solo para WSL/Ubuntu)

WeasyPrint requiere librerías del sistema. En WSL/Ubuntu, ejecuta:

```bash
bash install_weasyprint_deps.sh
```

Este script instala automáticamente todas las dependencias necesarias e instala `requirements.txt`.

### Paso 2: Crear entorno virtual (si no lo hizo el script anterior)

```bash
cd session-report-manger
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```bash
source .venv/bin/activate
export $(cat .env | xargs)
python -m streamlit run app/ui.py
```

## Información sensible protegida

⚠️ **NUNCA subir a git:**
- `.env` (credenciales)
- `data/` (información personal de alumnos)
- Archivos `.pdf` generados

✅ **Seguro subir a git:**
- Código fuente
- `.env.example` (sin credenciales)
- Plantillas HTML/CSS
- Configuración
