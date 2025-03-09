FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY app/ .

# Expose the port the app runs on
EXPOSE 8888

# Command to run the application
CMD ["python3", "chat.py"]
