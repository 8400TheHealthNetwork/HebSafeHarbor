import pytest
from presidio_analyzer.nlp_engine import NlpArtifacts
from spacy.tokens import Doc

from hebsafeharbor.common.city_utils import AMBIGUOUS_CITIES_CONTEXT, AMBIGOUS_BELOW_THRESHOLD_CITIES_LIST, \
    AMBIGOUS_ABOVE_THRESHOLD_CITIES_LIST
from hebsafeharbor.common.prepositions import LOCATION_PREPOSITIONS
from hebsafeharbor.identifier.signals.hebrew_city_recognizer import AmbiguousHebrewCityRecognizer


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

@pytest.mark.parametrize("words,score,entity_type", [(["לשכה", "עמוקה", "תאים"], 0.2, "CITY"),
                                                     (["הגיע", "לעמוקה"], 0.2, "CITY"),
                                                     ])
def test_city_simple(he_vocab, score, entity_type, words):
    mock_doc = Doc(he_vocab, words=words)
    nlp_artifacts = doc_to_nlp_artifact(mock_doc)
    ambiguous_cities_set = set(
        AMBIGOUS_BELOW_THRESHOLD_CITIES_LIST).union(
        set(AMBIGOUS_ABOVE_THRESHOLD_CITIES_LIST))
    city_recognizer = AmbiguousHebrewCityRecognizer("AmbiguousIsraeliCityRecognizer", "CITY",
                                                         ambiguous_cities_set,
                                                         allowed_prepositions=LOCATION_PREPOSITIONS,
                                                         endorsing_entities=['LOC', 'GPE'],
                                                         context=AMBIGUOUS_CITIES_CONTEXT)
    results = city_recognizer.analyze(text=mock_doc.text,
                                          entities=["CITY"],
                                          nlp_artifacts=nlp_artifacts)

    assert results[0].score == score
    assert results[0].entity_type == entity_type
