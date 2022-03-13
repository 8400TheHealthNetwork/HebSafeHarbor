import pytest
from presidio_analyzer import RecognizerRegistry, AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpArtifacts
from spacy.tokens import Doc

from hebsafeharbor.common.city_utils import AMBIGUOUS_CITIES_CONTEXT, AMBIGOUS_BELOW_THRESHOLD_CITIES_LIST, \
    AMBIGOUS_ABOVE_THRESHOLD_CITIES_LIST
from hebsafeharbor.common.prepositions import LOCATION_PREPOSITIONS
from hebsafeharbor.identifier import HebSpacyNlpEngine
from hebsafeharbor.identifier.signals.hebrew_city_recognizer import AmbiguousHebrewCityRecognizer

import logging

LOGGER = logging.getLogger(__name__)

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
def test_ambigous_city_simple(he_vocab, score, entity_type, words):
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

@pytest.mark.parametrize("text,score,entity_type,supportive_context_word,textual_explanation,case", [("רמות גלוקוז בצום", 0.2, "CITY","",None,"Test with no enhancement"),
                                                     ("הגיע לרמות", 0.6000000000000001, "CITY","הגיע", None,"Test enhancement with context"),
                                                     ("מטופל ממושב אודם", 0.6000000000000001, "CITY","","NLP-LOC-enhanced;", "Test enhancement with NLP artifacts"),
                                                     ])
def test_ambigous_city_enhanced(he_vocab, score, entity_type, text, supportive_context_word,textual_explanation,case):
    LOGGER.info(case)
    nlp_engine = HebSpacyNlpEngine()
    ambiguous_cities_set = set(
        AMBIGOUS_BELOW_THRESHOLD_CITIES_LIST).union(
        set(AMBIGOUS_ABOVE_THRESHOLD_CITIES_LIST))
    city_recognizer = AmbiguousHebrewCityRecognizer("AmbiguousIsraeliCityRecognizer", "CITY",
                                                         ambiguous_cities_set,
                                                         allowed_prepositions=LOCATION_PREPOSITIONS,
                                                         endorsing_entities=['LOC', 'GPE'],
                                                         context=AMBIGUOUS_CITIES_CONTEXT)

    registry = RecognizerRegistry()
    registry.add_recognizer(city_recognizer)

    analyzer_engine = AnalyzerEngine(registry=registry, nlp_engine=nlp_engine)
    results = analyzer_engine.analyze(text, language="he", return_decision_process=True)

    assert results[0].score == score
    assert results[0].entity_type == entity_type
    assert results[0].analysis_explanation.supportive_context_word == supportive_context_word
    assert results[0].analysis_explanation.textual_explanation == textual_explanation
