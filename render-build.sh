#!/usr/bin/env bash

# Install dependencies required for PDF and OCR
apt-get update && apt-get install -y tesseract-ocr poppler-utils

# Then install Python packages
pip install -r requirements.txt