# ==========================================
# 🦅 HUMAIN Lifestyle — Streamlit Frontend
# Production-ready Dockerfile
# ==========================================

FROM python:3.11-slim

# Disable Python buffering
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "streamlit_app.py"]
CMD ["--server.port=8501", "--server.address=0.0.0.0"]
