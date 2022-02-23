from typing import List
from presidio_analyzer import EntityRecognizer, RecognizerResult, AnalysisExplanation
from presidio_analyzer.nlp_engine import NlpArtifacts

from hebsafeharbor.common.terms_recognizer import TermsRecognizer


class LexiconBasedRecognizer(EntityRecognizer):
    """
    A class which extends the EntityRecognizer (@Presidio) and recognize entities based on a lexicon
    """

    DEFAULT_CONFIDENCE_LEVEL = 0.7  # expected confidence level for this recognizer

    def __init__(self, name: str, supported_entity: str, phrase_list: List[str], supported_language: str = "he",
                 allowed_prepositions=[]):
        """
        Initializes Hebrew LexiconBasedRecognizer

        :param name: recognizer's name
        :param supported_entity: entity type to be associated with the entities recognized by the lexicon based
        recognizer
        :param phrase_list: lexicon's phrases
        :param supported_language: the language that the recognizer supports. Hebrew is the default
        :param allowed_prepositions: prepositions that allowed to be recognized as part of the entity (in addition to
        the lexicon phrase itself). Empty list (which means prepositions are not allowed) is the default
        """
        super().__init__(name=name, supported_entities=[supported_entity], supported_language=supported_language)
        self.terms_recognizer = TermsRecognizer(phrase_list)
        self.allowed_prepositions = allowed_prepositions

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

        # Iterate over the Automaton offsets and create Recognizer result for each of them
        for start_offset, length in terms_offsets:
            result = RecognizerResult(
                entity_type=self.supported_entities[0],
                start=start_offset,
                end=start_offset + length,
                score=self.DEFAULT_CONFIDENCE_LEVEL,
                analysis_explanation=AnalysisExplanation(self.name, self.DEFAULT_CONFIDENCE_LEVEL),
                recognition_metadata={RecognizerResult.RECOGNIZER_NAME_KEY: self.name}
            )
            results.append(result)

        return results
