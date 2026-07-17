FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Expose the standard FastAPI port
EXPOSE 8000

# Run the startup script (migrates database, then starts FastAPI)
CMD ["./start.sh"]
