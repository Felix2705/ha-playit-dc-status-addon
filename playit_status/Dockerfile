FROM python:3.12-alpine

RUN apk add --no-cache ca-certificates

WORKDIR /addon

COPY requirements.txt /addon/
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /addon/
COPY run.sh /addon/
COPY app /addon/app
RUN chmod +x /addon/run.sh

CMD ["/addon/run.sh"]
