FROM python:3.9-alpine

RUN apk add tzdata build-base libffi-dev py3-cffi --no-cache

RUN mkdir -p /app/src
WORKDIR /app

ENV TZ=America/New_York
ENV VIRTUAL_ENV=/src/env
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV BOT_CONFIG_DIR="../config"
ENV BOT_DB_URL="sqlite:///../config/sqlite.db"
ENV BOT_ALEMBIC_CONFIG="./src/alembic"


RUN python -m venv $VIRTUAL_ENV
COPY requirements.txt /app/
RUN pip3 install -r requirements.txt


COPY ./src/ /app/src/
COPY main.py /app/
VOLUME /config

CMD ["python3", "main.py"]
