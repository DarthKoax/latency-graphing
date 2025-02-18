# Use an official lightweight Python image.
FROM python:3.9-slim

# Set working directory.
WORKDIR /app

# Copy the script into the container.
COPY main.py .

# When the container starts, run the script.
CMD ["python", "main.py"]
