FROM python:3.10-alpine

RUN apk add --no-cache git postgresql-dev gcc libc-dev
RUN apk add --no-cache gcc g++ make libffi-dev python3-dev build-base

RUN pip install gunicorn
RUN pip install psycopg2
RUN pip install ipdb
RUN pip install ipython

WORKDIR /app

RUN git clone -b fix/create-env https://github.com/Decide-chiquito/decide-part-chiquito.git .
RUN pip install -r requirements.txt

WORKDIR /app/decide

ADD .env /app/collecti_stamp/.env
ENV $(cat /app/collecti_stamp/.env | xargs)

# local settings.py
ADD docker-settings.py /app/decide/local_settings.py

RUN ./manage.py collectstatic
RUN find . -mindepth 2 -type d -path '*/static' -exec cp -r {}/. ./static \;

#CMD ["gunicorn", "-w 5", "decide.wsgi", "--timeout=500", "-b 0.0.0.0:5000"]
