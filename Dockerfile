# Base Image
FROM python:3.12-alpine

COPY requirements.txt /requirements.txt
RUN pip install --break-system-packages -r requirements.txt
COPY zm_onvif_datetime.py /zm_onvif_datetime.py

ENTRYPOINT [ "/bin/sh", "-c", "/zm_onvif_datetime.py ${@}", "--" ]
