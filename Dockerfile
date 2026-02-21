FROM python:3.8

WORKDIR /app1

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port (optional but good practice)
EXPOSE 10000

# Run your app
CMD ["python3", "main.py"]
