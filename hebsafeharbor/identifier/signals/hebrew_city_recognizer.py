import re
from typing import List
from presidio_analyzer import EntityRecognizer, RecognizerResult, AnalysisExplanation, LemmaContextAwareEnhancer
from presidio_analyzer.nlp_engine import NlpArtifacts

from hebsafeharbor.identifier.signals.lexicon_based_recognizer import LexiconBasedRecognizer


class AmbiguousHebrewCityRecognizer(LexiconBasedRecognizer):
    """
    A class which extends the EntityRecognizer (@Presidio) and recognize entities based on a lexicon
    and additional restrictions
    """

    DEFAULT_CONFIDENCE_LEVEL = 0.2  # expected confidence level for this recognizer
    LOCATION_OVERLAP_FACTOR = 0.8  # enhancement factor for this recognizer if overlap with another geo entity found

    def __init__(self, name: str, supported_entity: str, phrase_list: List[str], supported_language: str = "he",
                 endorsing_entities=List[str], allowed_prepositions=[], context=List[str]):
        """
        Initializes AmbiguousHebrewCityRecognizer

        :param name: recognizer's name
        :param supported_entity: entity type to be associated with the entities recognized by the lexicon based
        recognizer
        :param phrase_list: lexicon's phrases
        :param supported_language: the language that the recognizer supports. Hebrew is the default
        :param allowed_prepositions: prepositions that allowed to be recognized as part of the entity (in addition to
        the lexicon phrase itself). Empty list (which means prepositions are not allowed) is the default
        :param endorsing_entities: if recognized entity has overlap with at least one entity from this list,
        its score increases
        :param context: if any of words in the list are found around entity, its sore increases
        """
        super().__init__(name=name, supported_entity=supported_entity, phrase_list=phrase_list,
                         supported_language=supported_language, allowed_prepositions=allowed_prepositions)
        self.endorsing_entities = endorsing_entities
        self.context = context

    def load(self) -> None:
        """No loading is required."""
        pass

    def analyze(
            self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Recognize entities based on lexicon
        :param text: text for recognition
        :param entities: supported entities
        :param nlp_artifacts: artifacts of the nlp engine
        :return list of entities recognized based on the lexicon
        """
        results = []

        terms_offsets = self.terms_recognizer(text, prefixes=self.allowed_prepositions)

        if len(terms_offsets) == 0:
            return results

        # iterate over the spaCy tokens, and find all the position indices for endorsing entities
        geo_entities_position_set = set()
        for entity in nlp_artifacts.entities:
            if entity.label_ in self.endorsing_entities:
                for char in range(entity.start_char, entity.end_char):
                    geo_entities_position_set.add(char)

        # iterate over potential city offsets and endorse the results using overlap with geo-entities or support words
        for term_start, term_len in terms_offsets:
            overlap_ratio = len(
                set(range(term_start, term_start + term_len)).intersection(geo_entities_position_set)) / term_len
            adjusted_score = self.DEFAULT_CONFIDENCE_LEVEL + (overlap_ratio * self.LOCATION_OVERLAP_FACTOR)
            result = RecognizerResult(
                entity_type="CITY",
                start=term_start,
                end=term_start + term_len,
                score=adjusted_score,
                analysis_explanation=AnalysisExplanation(self.name, adjusted_score),
                recognition_metadata={RecognizerResult.RECOGNIZER_NAME_KEY: self.name},
            )

            results.append(result)

        return results
