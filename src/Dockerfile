# Use an official Python runtime as a parent image for ARM architecture
FROM --platform=linux/arm64 python:3.12-slim AS base

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy only the dependency files first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the application code
COPY . .

# Final stage
FROM --platform=linux/arm64 python:3.12-slim AS final

# Set the working directory in the container
WORKDIR /app

# Copy the installed dependencies from the base stage
COPY --from=base /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=base /usr/local/bin/poetry /usr/local/bin/poetry

# Make port 8050 available to the world outside this container
EXPOSE 8050

# Define environment variable
ENV NAME PortfolioAnalyzer

CMD ["poetry", "run", "python", "main.py"]