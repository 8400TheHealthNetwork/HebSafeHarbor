# using two stage build to save space, based on https://pythonspeed.com/articles/multi-stage-docker-python/

FROM python:3.9-slim AS compile-image

WORKDIR /usr/src/app
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc
RUN python3 -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements-streamlit.txt ./
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements-streamlit.txt


FROM python:3.9-slim AS build-image
WORKDIR /usr/src/app
COPY demo_app.py ./
COPY utils.py ./
COPY visualizer.py ./
COPY --from=compile-image /opt/venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
#run app and expose port 8501 for listening
EXPOSE 8501
ENTRYPOINT ["streamlit","run", "demo_app.py"]
