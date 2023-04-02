FROM debian:latest
COPY / /FCE_bot/
WORKDIR /FCE_bot
RUN apt-get update && apt-get --no-install-recommends install python3.9 pip -y
RUN python3 -m venv .venv
RUN source .venv/bin/activate
RUN pip install -r requirements.txt
RUN deactivate
ENTRYPOINT ["bash","scheduler.sh"]

