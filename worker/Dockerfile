FROM xserrat/facebook-demucs:latest

# Set working directory
WORKDIR /app

# Copy the application code to the container
COPY worker-server-2.py /app/worker-server.py

# Copy any requirements.txt if available
COPY requirements.txt /app/requirements.txt

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "worker-server.py"]
