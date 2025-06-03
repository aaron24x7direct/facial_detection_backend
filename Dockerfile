FROM python:3.11-slim

# Install dependencies and tesseract
RUN apt-get update && apt-get install -y tesseract-ocr libtesseract-dev

# Optional: install language data files if needed
# RUN apt-get install -y tesseract-ocr-eng

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Command to run your FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
