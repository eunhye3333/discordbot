# Base image
FROM python:3.9

# Set working directory in the container
WORKDIR /app

# Copy project files to the working directory
COPY Bot.py /app

# Install dependencies
RUN pip install --no-cache-dir discord

# Run the bot when the container starts
CMD ["python", "Bot.py"]