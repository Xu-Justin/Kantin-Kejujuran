FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && \
    apt-get install -y git vim libgtk2.0-dev zip unzip && \
    rm -rf /var/cache/apk/*

WORKDIR /apps

COPY requirements.txt .
RUN pip --no-cache-dir install -r requirements.txt

COPY templates templates
COPY sample_images sample_images
COPY ./*.py ./

EXPOSE 8000

ENTRYPOINT [ "python3", "main.py" ]