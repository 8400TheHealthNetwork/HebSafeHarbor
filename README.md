# HebSafeHarbor

A de-identification toolkit for clinical text in Hebrew.

## Installation

To install the package, clone the repo and install all dependencies, preferably in a virtual environment:

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

1. Run the following command to install and run the server and demo services:

```sh
docker-compose up -d --build
```

2. Navigate in the browser <http://localhost:8080/docs> to test the Server swagger
3. Navigate in the browser <http://localhost:8501> to test the Demo app
