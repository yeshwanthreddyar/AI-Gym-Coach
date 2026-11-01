FROM python:3.11-slim
WORKDIR /srv
COPY requirements.txt requirements-cv.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-cv.txt
COPY app ./app
ENV GYM_DB=/data/gym.db
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
