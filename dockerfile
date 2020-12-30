FROM python:3.7

ENV BANK_BLZ BANK_BLZ
ENV BANK_USERNAME BANK_USERNAME
ENV BANK_PIN BANK_PIN
ENV BANK_URL BANK_URL
ENV FIREFLY_URL FIREFLY_URL
ENV FIREFLY_TOKEN FIREFLY_TOKEN

WORKDIR /app
COPY script.py /app/script.py
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

CMD [ "python", "./script.py" ]