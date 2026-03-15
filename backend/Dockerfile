FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///./data/nextmeal.db

# Expose port
EXPOSE 8000

# Run migrations and seed data on startup, then start server
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed_data && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
