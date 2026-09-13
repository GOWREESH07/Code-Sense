FROM python:3.11-slim

WORKDIR /app

# Only git is needed for cloning public repositories; skip heavy C++ compilers
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install xgboost with --no-deps to prevent downloading 340MB+ of unused nvidia CUDA libraries,
# then install remaining pure Python & CPU wheels
RUN pip install --no-cache-dir --no-deps xgboost>=2.0.0 && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Link /app/backend -> /app so 'from backend.*' imports resolve cleanly
RUN ln -s /app /app/backend

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
