# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Run uvicorn - Cloud Run will provide PORT env var
# Use shell form to access environment variable
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}

