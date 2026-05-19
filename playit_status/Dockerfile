FROM python:3.11-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /addon

COPY requirements.txt /addon/
RUN pip install --no-cache-dir -r requirements.txt

COPY poll.py /addon/
COPY run.sh /addon/
RUN chmod +x /addon/run.sh

CMD ["/addon/run.sh"]
