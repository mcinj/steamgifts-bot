FROM python:3.9-alpine

RUN mkdir -p /app
WORKDIR /app

RUN apk add tzdata build-base libffi-dev py3-cffi --no-cache

ENV TZ=America/New_York
ENV VIRTUAL_ENV=/app/env
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python -m venv $VIRTUAL_ENV
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY ./src/ /app/
VOLUME /config

CMD ["python3", "run.py"]
