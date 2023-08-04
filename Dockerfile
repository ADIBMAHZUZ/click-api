FROM python:3.7-alpine

ENV PYTHONUNBUFFERED 1

ENV APP_HOME=/click-api

COPY ./requirements.txt $APP_HOME/requirements.txt

WORKDIR $APP_HOME

COPY ./ $APP_HOME

RUN apk add --no-cache --virtual .build-deps \
    ca-certificates gcc postgresql-dev linux-headers musl-dev \
    libffi-dev jpeg-dev zlib-dev

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn eventlet 'gunicorn[eventlet]'

RUN apk add --upgrade --no-cache ffmpeg

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# CMD ["gunicorn", "click.wsgi:application", "--bind", "0.0.0.0:8000", "-k", "eventlet", "-w", "8"]