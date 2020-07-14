FROM python:3.7-alpine
FROM ubuntu:latest

WORKDIR /SubGen

ENV FLASK_APP App.py
ENV FLASK_RUN_HOST 127.0.0.1

RUN mkdir /SubGen/files

RUN apt-get update && apt-get upgrade
RUN apt-get --assume-yes install python3 python3-pip redis-server ffmpeg
RUN pip3 install pep517

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
