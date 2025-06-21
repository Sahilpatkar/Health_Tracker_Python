FROM python:3.11-slim
LABEL authors="spatkar"

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit","run","healthTrackerAppStreamlit.py","--server.port=8501","--server.enableCORS=false"]