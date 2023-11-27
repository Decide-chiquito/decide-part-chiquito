FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git libpq-dev gcc libc-dev gcc g++ make libffi-dev python3-dev build-essential && \
    apt-get clean

WORKDIR /app

RUN git clone https://github.com/Decide-chiquito/decide-part-chiquito.git . && \
    pip install --no-cache-dir -r requirements.txt

WORKDIR /app/decide

# local settings.py
COPY docker-settings.py /app/decide/local_settings.py

RUN ./manage.py collectstatic

# CMD ["gunicorn", "-w", "5", "decide.wsgi", "--timeout=500", "-b", "0.0.0.0:5000"]


