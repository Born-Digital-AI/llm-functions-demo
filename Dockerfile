FROM python:3.11-slim-buster 

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install  -r requirements.txt

COPY . /app/

EXPOSE 8822

CMD sh -c 'uvicorn main:app --host 0.0.0.0 --port 8822'
