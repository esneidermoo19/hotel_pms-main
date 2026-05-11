FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PORT=5000
ENV WEB_CONCURRENCY=3

# Expose port
EXPOSE 5000

# Run with gunicorn
# Note: we use run:app because run.py creates the 'app' object
# Optimization: Using multiple workers and threads
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
