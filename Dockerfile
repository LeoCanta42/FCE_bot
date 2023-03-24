FROM debian:latest
COPY / /FCE_bot/
WORKDIR /FCE_bot
RUN apt-get update && apt-get --no-install-recommends install python3.9 pip -y
RUN pip install -r requirements.txt
ENTRYPOINT ["bash","scheduler.sh"]

