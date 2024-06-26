FROM lsiobase/debian:bookworm

WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt update && apt install -y python3 chromium python3-pip chromium-sandbox --no-install-recommends &&  \
    pip install -r requirements.txt --upgrade --break-system-packages

COPY app /app/app
COPY setup.py /app/setup.py
RUN pip install -e . --break-system-packages
COPY root/ /


EXPOSE 5500
ENTRYPOINT ["/init"]
