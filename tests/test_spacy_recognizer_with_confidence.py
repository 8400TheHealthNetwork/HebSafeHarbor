import copy

import pytest
from presidio_analyzer.nlp_engine import NlpArtifacts
from spacy.tokens import Span, Doc

from hebsafeharbor.identifier.signals import SpacyRecognizerWithConfidence


@pytest.fixture(autouse=True)
def remove_extension():
    """
    Remove extensions as it is global
    """
    if Span.has_extension("confidence_score"):
        Span.remove_extension("confidence_score")


def doc_to_nlp_artifact(doc: Doc, language: str = "he") -> NlpArtifacts:
        lemmas = [token.lemma_ for token in doc]
        tokens_indices = [token.idx for token in doc]
        entities = list(doc.ents)
        return NlpArtifacts(
            entities=entities,
            tokens=doc,
            tokens_indices=tokens_indices,
            lemmas=lemmas,
            nlp_engine=None,
            language=language,
        )


def test_spacy_with_confidence_simple(he_vocab):
    Span.set_extension("confidence_score", default=1.0, force=True)
    mock_doc = Doc(he_vocab, words=["שלום", "כיתה", "אלף"])
    mock_doc.ents = [Span(mock_doc, 0, 1, label="PERSON"), Span(mock_doc, 1, 2, label="LOC")]
    mock_doc.ents[0]._.confidence_score = 0.666
    mock_doc.ents[1]._.confidence_score = 0.999

    nlp_artifacts = doc_to_nlp_artifact(mock_doc)

    hebspacy_recognizer = SpacyRecognizerWithConfidence(supported_language="he")
    results = hebspacy_recognizer.analyze(text=mock_doc.text,
                                          entities=["PERSON", "LOCATION"],
                                          nlp_artifacts=nlp_artifacts)

    assert len(results) == 2
    assert results[0].score == 0.666
    assert results[0].entity_type == "PERSON"
    assert results[1].score == 0.999
    assert results[1].entity_type == "LOCATION"


def test_spacy_without_confidence_raises_error(he_vocab):
    mock_doc = Doc(he_vocab, words=["חיים", "כיתה", "אלף"])
    mock_doc.ents = [Span(mock_doc, 0, 1, label="PERSON")]
    nlp_artifacts = doc_to_nlp_artifact(mock_doc)

    hebspacy_recognizer = SpacyRecognizerWithConfidence(supported_language="he")

    with pytest.raises(ValueError):
        hebspacy_recognizer.analyze(text=mock_doc.text, entities=["PERSON"], nlp_artifacts=nlp_artifacts)
