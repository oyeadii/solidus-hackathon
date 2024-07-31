FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed system dependencies
RUN apt-get update
RUN rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies from requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

WORKDIR /app
EXPOSE 8000
# Run app.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "5", "--log-level", "debug"]
