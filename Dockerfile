FROM python:3-alpine

RUN apk add --no-cache openrc dbus bluez \
	&& mkdir /run/openrc \
	&& touch /run/openrc/softlevel

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

CMD ["sh", "-c", "./docker.sh"]
