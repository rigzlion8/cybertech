FROM python:3.11-slim

# Install system dependencies including nmap
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nmap \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create reports directory
RUN mkdir -p reports

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application with gunicorn
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 300 --worker-class sync

