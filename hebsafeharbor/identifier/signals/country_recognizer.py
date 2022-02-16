from typing import List
from presidio_analyzer import EntityRecognizer, RecognizerResult, AnalysisExplanation
from presidio_analyzer.nlp_engine import NlpArtifacts
from hebsafeharbor.common.country_utils import COUNTRY_DICT

import re

from hebsafeharbor.common.location_utils import LOCATION_PREPOSITIONS
from hebsafeharbor.common.terms_recognizer import TermsRecognizer

class CountryRecognizer(EntityRecognizer):
    """
    A class which extends the EntityRecognizer (@Presidio) and responsible for the recognition of countries.
    """

    DEFAULT_CONFIDENCE_LEVEL = 0.7  # expected confidence level for this recognizer

    def __init__(self, supported_language: str = "he",):
        """
        Initializes Hebrew CountryRecognizer
        """
        super().__init__(supported_entities=['COUNTRY'],
                       supported_language=supported_language,
                       )
        self.country_terms_recognizer = TermsRecognizer(COUNTRY_DICT.keys())
        self.country_prepositions = LOCATION_PREPOSITIONS

    def load(self) -> None:
        """No loading is required."""
        pass

    def analyze(
            self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Analyzes LOC and GPE entities to find spans which represent countries.
        """
        results = []

        country_offsets = self.country_terms_recognizer(text, prefixes=self.country_prepositions)

        # iterate over the Automaton offsets, and call `token.like_num`
        for start_char, length in country_offsets:
            result = RecognizerResult(
                entity_type="COUNTRY",
                start=start_char,
                end=start_char + length,
                score=self.DEFAULT_CONFIDENCE_LEVEL,
                analysis_explanation = AnalysisExplanation(self.name, 1.0)
            )
            results.append(result)

        return results