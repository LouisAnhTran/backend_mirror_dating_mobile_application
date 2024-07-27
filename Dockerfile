# Use the official Python image from the DockerHub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI application to the container
COPY . .

# Specify the command to run the application
CMD ["python", "main.py"]
