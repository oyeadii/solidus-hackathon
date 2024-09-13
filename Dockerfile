# Use the official Python 3.9 slim image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the necessary ports
EXPOSE 8888  
EXPOSE 8000  

# Create a script to handle Jupyter token extraction and FastAPI start
RUN echo '#!/bin/bash\n'\
    'echo "Starting Jupyter Notebook..."\n'\
    'jupyter notebook --ip=0.0.0.0 --no-browser --allow-root > /app/jupyter.log 2>&1 &\n'\
    'sleep 10  # Wait for Jupyter to start\n'\
    'echo "Checking if Jupyter log exists..."\n'\
    '[ -f /app/jupyter.log ] && echo "Log file exists" || { echo "Error: Log file not found"; exit 1; }\n'\
    'echo "Extracting Jupyter token using Python..."\n'\
    'python3 /app/extract_token.py\n'\
    'if [ $? -ne 0 ]; then\n'\
    '    echo "Error: Unable to extract Jupyter token."\n'\
    '    exit 1\n'\
    'fi\n'\
    'echo "Starting FastAPI..."\n'\
    'uvicorn main:app --host 0.0.0.0 --port 8000\n' > /start.sh

# Make the script executable
RUN chmod +x /start.sh

# Set the default command to run the script
CMD ["/bin/bash", "/start.sh"]
