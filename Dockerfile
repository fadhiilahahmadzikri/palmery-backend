FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user (Hugging Face Spaces requires this for safety)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy the rest of the application
COPY --chown=user . $HOME/app/

# Make port 8000 the default, but allow overriding via PORT env var
ENV PORT=8000
EXPOSE $PORT

# Run the FastAPI application with Uvicorn, using the PORT environment variable
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
