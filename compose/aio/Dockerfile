FROM python:3.6-stretch

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  && apt-get -y install gcc python3-dev \
  && apt-get -y install postgresql-client \
  # git support to install python packages from Github
  && apt-get -y install git

RUN adduser aio

# Requirements are installed here to ensure they will be cached.
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt \
    && rm /requirements.txt

COPY ./compose/aio/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint
RUN chown aio /entrypoint

COPY ./compose/aio/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start
RUN chown aio /start

COPY . /app

RUN chown -R aio /app

USER aio

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
