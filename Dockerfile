FROM python:3.12-slim as base
# RUN pip install --no-cache-dir --upgrade pip
RUN /usr/local/bin/python -m pip install --no-cache-dir --upgrade pip setuptools wheel
COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

WORKDIR /usr/app

COPY ./scraping ./

CMD ["python", "scraping/main.py"]

