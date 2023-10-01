FROM python:3-slim-bullseye
ENV deb=wkhtmltox_0.12.6.1-2.bullseye_arm64.deb
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
RUN pip install --upgrade pip

RUN adduser monbot
USER monbot
WORKDIR /home/monbot

COPY --chown=monbot:monbot requirements.txt requirements.txt
ENV PATH="/home/monbot/.local/bin:${PATH}"

RUN pip install --user -r requirements.txt

COPY --chown=monbot:monbot . .
USER root
RUN apt update -y && apt install chromium -y --no-install-recommends && apt install -y ./$deb && rm $deb && unset deb
USER monbot
RUN mkdir -p /home/monbot/.local/share/pyppeteer/local-chromium/588429/chrome-linux &&\
        ln -sfv $(which chromium) /home/monbot/.local/share/pyppeteer/local-chromium/588429/chrome-linux/chrome
EXPOSE 8443
VOLUME ["/home/monbot/bot/recurrent.json"]

CMD ["python", "main.py"]
