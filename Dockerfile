# using two stage build to save space, based on https://pythonspeed.com/articles/multi-stage-docker-python/

FROM python:3.9-slim AS compile-image

WORKDIR /usr/src/app
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc
RUN python3 -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
COPY requirements-server.txt ./
COPY setup.py ./
COPY README.md ./
COPY hebsafeharbor ./hebsafeharbor
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt --no-cache-dir
RUN python3 -m pip install -r requirements-server.txt --no-cache-dir
RUN python3 setup.py install


FROM python:3.9-slim AS build-image
WORKDIR /usr/src/app
COPY hsh_service.py ./
COPY server.py ./
COPY --from=compile-image /opt/venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
#run server and expose port 8000 for listening
EXPOSE 8000
ENTRYPOINT ["python","server.py"]
