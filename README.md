# HebSafeHarbor

A de-identification toolkit for clinical text in Hebrew.

[![MIT license](https://img.shields.io/badge/license-MIT-brightgreen.svg)](http://opensource.org/licenses/MIT) ![Release](https://img.shields.io/github/v/release/8400TheHealthNetwork/HebSafeHarbor.svg) [![PyPI version](https://badge.fury.io/py/hebsafeharbor.svg)](https://badge.fury.io/py/hebsafeharbor) [![Pypi Downloads](https://img.shields.io/pypi/dm/hebsafeharbor.svg)](https://img.shields.io/pypi/dm/hebsafeharbor.svg) 

HebSafeHarbor was developed according to the requirements described in הצעה למתווה התממה של טקסט רפואי - נמל מבטחים (read more [here](docs/))

The toolkit integrates and uses open source libraries and assets, including [HebSpacy](https://github.com/8400TheHealthNetwork/HebSpacy), [Presidio](https://microsoft.github.io/presidio/), Wikipedia and public lexicons.



## Installation

To install the package, run the following commands - preferably in a virtual environment
``` sh
# Create conda env (optional)
conda create --name hebsafeharbor python=3.8
conda activate hebsafeharbor

# Install HebSafeHarbor
pip install hebsafeharbor

# Download the he_ner_news_trf model used by hebsafeharbor
pip install https://github.com/8400TheHealthNetwork/HebSpacy/releases/download/he_ner_news_trf-3.2.1/he_ner_news_trf-3.2.1-py3-none-any.whl
```

Alternatively, you may clone the repo and install all dependencies:

``` sh
# Create conda env (optional)
conda create --name hebsafeharbor python=3.8
conda activate hebsafeharbor

# Install dependencies
pip install -r requirements.txt

# (Optional) Install package locally
pip install -e .

# Download the he_ner_news_trf model used by hebsafeharbor
pip install https://github.com/8400TheHealthNetwork/HebSpacy/releases/download/he_ner_news_trf-3.2.1/he_ner_news_trf-3.2.1-py3-none-any.whl
```

## Getting started

### Python

```python
from hebsafeharbor import HebSafeHarbor

hsh = HebSafeHarbor()

text = """שרון לוי התאשפזה ב02.02.2012 וגרה בארלוזרוב 16 רמת גן"""
doc = {"text": text}

output = hsh([doc])

print(output)
```

### Docker 
HebSafeHarbor can expose REST endpoint for the service using [FastAPI](https://fastapi.tiangolo.com/) and Docker. 
To download the Docker container, run the following command:
```bash
# Download image
docker pull hebsafeharbor/hebsafeharbor

# Run containers with default port
docker run -d -p 8080:8080 hebsafeharbor/hebsafeharbor:latest
```
Navigate in the browser to `localhost:8080/docs` to access the service swagger and learn more about the input and output schemes.

For experimentation and testing purposes, we provide a [Streamlit](https://streamlit.io/) demo application that queries the service and visualizes the result 
![](images/demo_application.png)
To download the Docker container, run the following command:
```sh
# Download image
docker pull hebsafeharbor/demo_application

# Run containers with default port
docker run -d -p 8501:8501 hebsafeharbor/demo_application:latest
```
Navigate to `localhost:8501` to access the demo application.

### Docker Compose
HebSafeHarbor and the demo application containers are also available in docker-compose setup.

Run the `docker-compose` command against the `docker-compose.yml` file in the root directory to get the latest containers from Docker Hub
```sh
docker-compose up -d --build
```
Navigate in the browser to <https://server.localhost/docs> to access the service swagger.
Navigate in the browser to <https://demo.localhost> to test the demo application.


#### Development mode
To run the containers against the repo's code, run the following command:
```sh
docker-compose -f docker-compose-development.yml up -d --build
```

-----

HebSafeHarbor is an open-source project developed by [8400 The Health Network](https://www.8400thn.org/).
