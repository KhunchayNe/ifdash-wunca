FROM debian:sid
RUN echo 'deb http://mirror.psu.ac.th/debian/ sid main contrib non-free non-free-firmware' > /etc/apt/sources.list
RUN echo 'deb http://mirror.kku.ac.th/debian/ sid main contrib non-free non-free-firmware' >> /etc/apt/sources.list

RUN apt-get update && apt-get upgrade -y

RUN apt install -y python3 python3-dev python3-pip python3-venv npm git locales
RUN sed -i '/th_TH.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8 

RUN python3 -m venv /venv
ENV PYTHON=/venv/bin/python3
RUN $PYTHON -m pip install wheel poetry gunicorn

WORKDIR /app

ENV IFDASH_SETTINGS=/app/ifdash-production.cfg

COPY ifdash/cmd /app/ifdash/cmd
COPY poetry.lock pyproject.toml /app/

RUN . /venv/bin/activate \
	&& poetry config virtualenvs.create false \
	&& poetry install --no-interaction --only main

COPY ifdash/web/static/package.json ifdash/web/static/package-lock.json ifdash/web/static/
RUN npm install --prefix ifdash/web/static

COPY . /app

RUN apt autoremove && apt autoclean && rm -rf /var/cache/apt/archives /var/lib/apt/lists/*
