from typing import List
from presidio_analyzer import EntityRecognizer, RecognizerResult, AnalysisExplanation
from presidio_analyzer.nlp_engine import NlpArtifacts
from hebsafeharbor.common.city_utils import BELOW_THRESHOLD_CITIES_LIST, ABOVE_THRESHOLD_CITIES_LIST, ABBREVIATIONS_LIST

import re

from hebsafeharbor.common.location_utils import LOCATION_PREPOSITIONS
from hebsafeharbor.common.terms_recognizer import TermsRecognizer



class IsraeliCityRecognizer(EntityRecognizer):
    """
    A class which extends the EntityRecognizer (@Presidio) and responsible for the recognition of cities in Israel.
    """

    DEFAULT_CONFIDENCE_LEVEL = 0.7  # expected confidence level for this recognizer

    def __init__(self, supported_language: str = "he", ):
        """
        Initializes IsraeliCityRecognizer
        """
        super().__init__(supported_entities=['CITY'],
                         supported_language=supported_language,
                         )
        cities_list = set(BELOW_THRESHOLD_CITIES_LIST).union(set(ABOVE_THRESHOLD_CITIES_LIST)).union(
            set(ABBREVIATIONS_LIST))
        self.city_terms_recognizer = TermsRecognizer(cities_list)
        self.city_prepositions = LOCATION_PREPOSITIONS

    def load(self) -> None:
        """No loading is required."""
        pass

    def analyze(
            self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Analyzes LOC and GPE entities to find spans which represent cities in Israel.
        """
        results = []

        city_offsets = self.city_terms_recognizer(text, prefixes=self.city_prepositions)

        # iterate over the Automaton offsets, and call `token.like_num`
        for start_char, length in city_offsets:
            result = RecognizerResult(
                entity_type="CITY",
                start=start_char,
                end=start_char + length,
                score=self.DEFAULT_CONFIDENCE_LEVEL,
                analysis_explanation=AnalysisExplanation(self.name, 1.0)
            )
            results.append(result)

        return results
