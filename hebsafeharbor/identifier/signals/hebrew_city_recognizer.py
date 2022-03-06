from typing import List, Set
from presidio_analyzer import RecognizerResult, AnalysisExplanation
from presidio_analyzer.nlp_engine import NlpArtifacts

from hebsafeharbor.common.context_terms_recognizer import ContextTermsRecognizer
from hebsafeharbor.identifier.signals.lexicon_based_recognizer import LexiconBasedRecognizer


class AmbiguousHebrewCityRecognizer(LexiconBasedRecognizer):
    """
    A class which extends the EntityRecognizer (@Presidio) and recognize entities based on a lexicon
    and additional restrictions
    """

    DEFAULT_CONFIDENCE_LEVEL = 0.2  # expected confidence level for this recognizer
    LOCATION_OVERLAP_FACTOR = 0.4  # enhancement factor for this recognizer if overlap with another geo entity found

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
        self.context_recognizer = ContextTermsRecognizer(context) if context else None

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

        # iterate over potential city offsets and endorse the results using overlap with geo-entities or support words
        for term_start, term_len in terms_offsets:
            result = RecognizerResult(
                entity_type="CITY",
                start=term_start,
                end=term_start + term_len,
                score=self.DEFAULT_CONFIDENCE_LEVEL,
                analysis_explanation=AnalysisExplanation(self.name, self.DEFAULT_CONFIDENCE_LEVEL),
                recognition_metadata={RecognizerResult.RECOGNIZER_NAME_KEY: self.name},
            )

            results.append(result)

        results = self.enhance_using_other_entities(nlp_artifacts, results)

        return results

    @staticmethod
    def _extract_geo_entities(nlp_artifacts: NlpArtifacts, entity_names: List[str]) -> Set[int]:
        """
        Identify positions of other entities in a text that can provide context for entity
        :param nlp_artifacts: artifacts of the nlp engine
        :param entity_names: list of entity names
        :return set of positions in a text string corresponding provided entity names
        """
        geo_entities_positions = set()
        for entity in nlp_artifacts.entities:
            if entity.label_ in entity_names:
                for char in range(entity.start_char, entity.end_char):
                    geo_entities_positions.add(char)
        return geo_entities_positions

    def enhance_using_other_entities(self, nlp_artifacts: NlpArtifacts, results: List[RecognizerResult]):
        """
        Iterate over the spaCy tokens, and find all the position indices for endorsing entities
        :param nlp_artifacts: artifacts of the nlp engine
        :param results: list of preliminary recognizer results
        :return list of results, enhanced where there is an overlap with geo entity
        """
        geo_entities_positions = self._extract_geo_entities(nlp_artifacts, self.endorsing_entities)
        if not geo_entities_positions:
            return results

        for result in results:
            overlap_ratio = len(
                set(range(result.start, result.end)).intersection(geo_entities_positions)) / (result.end - result.start)
            adjusted_score = result.score + (overlap_ratio * self.LOCATION_OVERLAP_FACTOR)
            if adjusted_score != result.score:
                result.score = adjusted_score
                result.analysis_explanation.set_improved_score(adjusted_score)
                result.analysis_explanation.append_textual_explanation_line("NLP-LOC-enhanced;")

        return results
