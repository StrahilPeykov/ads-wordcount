FROM python:3.11-slim-bullseye

# Update package lists
RUN apt-get update

# Install any additional packages if needed
# RUN apt-get install -y "any package you like"

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Set working directory
WORKDIR /app

# Keep container running
CMD [ "/bin/bash", "-c", "while true; do bash -l; done" ]