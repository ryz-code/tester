FROM python:3-slim

ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NOWARNINGS="yes"

RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-utils aria2 procps ffmpeg git curl && \
    curl -Ls https://github.com/Oxhellfire/pymegasdkrest/releases/download/v6.9/megasdkrest -o /usr/local/bin/megasdkrest && \
    chmod +x /usr/local/bin/megasdkrest

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "-m", "drive1bot" ]
