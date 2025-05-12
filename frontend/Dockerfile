FROM python:3.10-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (if your app uses a specific port)
EXPOSE 5000

# Run the application
CMD ["python", "-m", "src.app"]