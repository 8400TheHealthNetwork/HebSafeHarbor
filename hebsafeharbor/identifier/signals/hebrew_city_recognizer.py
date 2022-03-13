from typing import List, Set, Optional
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
    CONTEXT_ENHANCEMENT_FACTOR = 0.4  # enhancement factor for this recognizer if supportive context found

    def __init__(self, name: str, supported_entity: str, phrase_list: List[str], supported_language: str = "he",
                 endorsing_entities:List[str]=None, allowed_prepositions: List[str]=None, context:List[str] = None):
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
        self.endorsing_entities = endorsing_entities if endorsing_entities else []
        self.context = context if context else []
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

    def enhance_using_context(
        self,
        text: str,
        raw_recognizer_results: List[RecognizerResult],
        other_raw_recognizer_results: List[RecognizerResult],
        nlp_artifacts: NlpArtifacts,
        context: Optional[List[str]] = None,
    ) -> List[RecognizerResult]:
        """Overrides generic context enhancer with recognizer-specific.
        Enhance confidence score using context of the entity.

        in case a result score is boosted, derived class need to update
        result.recognition_metadata[RecognizerResult.IS_SCORE_ENHANCED_BY_CONTEXT_KEY]

        :param text: The actual text that was analyzed
        :param raw_recognizer_results: This recognizer's results, to be updated
        based on recognizer specific context.
        :param other_raw_recognizer_results: Other recognizer results matched in
        the given text to allow related entity context enhancement
        :param nlp_artifacts: The nlp artifacts contains elements
                              such as lemmatized tokens for better
                              accuracy of the context enhancement process
        :param context: list of context words
        """

        for result in raw_recognizer_results:
            result.recognition_metadata[RecognizerResult.IS_SCORE_ENHANCED_BY_CONTEXT_KEY] = True
            word = text[result.start:result.end]

            sentence = self.__extract_sentence_containing_position(
                nlp_artifacts=nlp_artifacts, start=result.start
            )

            if sentence != "":
                supportive_context = self.__find_supportive_context_in_sentence(
                    sentence, word
                )
                if supportive_context:
                    result.score += self.CONTEXT_ENHANCEMENT_FACTOR

                    # Update the explainability object with context information
                    # helped improving the score
                    result.analysis_explanation.set_supportive_context_word(
                        supportive_context
                    )
                    result.analysis_explanation.set_improved_score(result.score)

        return raw_recognizer_results

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

    @staticmethod
    def __extract_sentence_containing_position(nlp_artifacts: NlpArtifacts, start: int) -> str:
        """
        Extracting the sentence which contains the start position of recognized entity using sentences from nlp_artifacts
        :param nlp_artifacts: An abstraction layer which holds different
                              items which are the result of a NLP pipeline
                              execution on a given text
        :param start: The start index of the word in the original text
        :return: sentence string
        """
        for sent in nlp_artifacts.tokens.sents:
            if (start >= sent.start_char) & (start <= sent.end_char):
                return sent.text
        return ''

    def __find_supportive_context_in_sentence(self, sentence: str, word: str):
        """
        Extracting the sentence which contains the start position of recognized entity using sentences from nlp_artifacts
        :param sentence: sentence string
        :param word: recognized entity string
        :return: details of supportive context recognized
        """
        # Sanity
        if not self.context_recognizer:
            return None
        if self.allowed_prepositions:
            prep = self.allowed_prepositions
        else:
            prep = None

        contexts = self.context_recognizer(sentence, word, prep)
        return contexts
