FROM python:3.10.4-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /usr/src/app/
WORKDIR /usr/src/app/

RUN apt-get update && apt-get install --fix-missing -y \
    build-essential libssl-dev xvfb curl wget nginx supervisor \
    libffi-dev libpq-dev python-dev gcc gettext unzip \
    daemonize dbus-user-session fontconfig aptitude gdal-bin \
    libgdal-dev python3-gdal binutils libproj-dev

# Adding trusting keys to apt for repositories
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -

# Adding Google Chrome to the repositories
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# Updating apt to see and install Google Chrome
RUN apt-get update && apt-get install --fix-missing -y google-chrome-stable

COPY ./requirements.txt ./requirements.txt
RUN pip install -U pip && pip install -r requirements.txt
COPY . .

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
RUN service nginx start

COPY celery_conf/celeryd /etc/default/celeryd
COPY celery_conf/celeryd.init /etc/init.d/celeryd
RUN chmod 777 /etc/init.d/celeryd

ENTRYPOINT ["sh", "./entrypoint.sh"]