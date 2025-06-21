FROM python:3.9-slim

WORKDIR /app

# Install system dependencies required for OpenCV and barcode libraries
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libdmtx0b \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directories for uploads and outputs
RUN mkdir -p uploads outputs

# Expose the port the app runs on
EXPOSE 5001

# Command to run the application
CMD ["python", "app-simplified.py"]