FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY fitness_metrics.py .
COPY recommendations.py .
COPY data/ ./data/
COPY backend/ ./backend/

# Copy food_items.xlsx if it exists (optional seed)
COPY food_items.xls[x] ./

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
