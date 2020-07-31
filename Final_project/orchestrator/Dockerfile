FROM python:3.7-slim-stretch

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
RUN mkdir -p /orch
COPY ./requirements.txt /orch/requirements.txt
RUN pip3 install -r /orch/requirements.txt
COPY . /orch
WORKDIR /orch
