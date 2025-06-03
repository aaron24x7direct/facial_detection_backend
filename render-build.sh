#!/usr/bin/env bash
set -o errexit

# Install system packages
apt-get update && apt-get install -y tesseract-ocr poppler-utils

# Install Python dependencies
pip install -r requirements.txt
