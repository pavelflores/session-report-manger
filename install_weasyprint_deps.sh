#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  libpango-1.0-0 \
  libpangoft2-1.0-0 \
  libcairo2 \
  libgdk-pixbuf-2.0-0 \
  libffi-dev \
  shared-mime-info \
  fontconfig \
  libharfbuzz-dev \
  libfribidi-dev \
  libjpeg-dev \
  libpng-dev \
  libfreetype6-dev

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Instalación completada. Ahora puedes ejecutar:"
echo "python generate_report.py"
