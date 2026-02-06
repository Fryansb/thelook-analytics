FROM python:3.12-slim

RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /code/entrypoint.sh

ENTRYPOINT ["/code/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
