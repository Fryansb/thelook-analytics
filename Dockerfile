FROM python:3.12-slim
WORKDIR /code
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["bash", "-c", "python manage.py migrate && python manage.py simulate_data && python manage.py runserver 0.0.0.0:8000"]
