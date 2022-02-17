import pytest
import spacy


@pytest.fixture(scope="session")
def he_vocab():
    return spacy.util.get_lang_class("he")().vocab
