import re
from typing import List, Set, Optional
from presidio_analyzer import RecognizerResult, AnalysisExplanation
from presidio_analyzer.nlp_engine import NlpArtifacts

from hebsafeharbor.common.terms_recognizer import TermsRecognizer
from hebsafeharbor.identifier.signals.lexicon_based_recognizer import LexiconBasedRecognizer


class AmbiguousHebrewCityRecognizer(LexiconBasedRecognizer):
    """
    A class which extends the EntityRecognizer (@Presidio) and recognize entities based on a lexicon
    and additional restrictions
    """

    def __init__(self, name: str, supported_entity: str, phrase_list: List[str], supported_language: str = "he",
                 endorsing_entities: List[str] = None, allowed_prepositions: List[str] = None, context: List[str] = None,
                 default_confidence_level: float = 0.2,
                 location_overlap_factor: float = 0.4, context_enhancement_factor: float = 0.4,
                 ):
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
        :param default_confidence_level: expected confidence level for this recognizer
        :param location_overlap_factor: enhancement factor for this recognizer if overlap with another geo entity found
        :param context_enhancement_factor: enhancement factor for this recognizer if supportive context found
        """
        super().__init__(name=name, supported_entity=supported_entity, phrase_list=phrase_list,
                         supported_language=supported_language, allowed_prepositions=allowed_prepositions)
        self.endorsing_entities = endorsing_entities if endorsing_entities else []
        self.context = context if context else []
        self.context_recognizer = TermsRecognizer(context) if context else None
        self.default_confidence_level = default_confidence_level
        self.location_overlap_factor = location_overlap_factor
        self.context_enhancement_factor = context_enhancement_factor

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
                score=self.default_confidence_level,
                analysis_explanation=AnalysisExplanation(self.name, self.default_confidence_level),
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
        Enhance confidence score using strictly defined context words and prepositions before the entity.
        Recognizer-specific enhancement in this case produces less results
        than default engine-level LemmaBasedContextEnhancer

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
            # Turn on IS_SCORE_ENHANCED_BY_CONTEXT_KEY flag,
            # to avoid result being additionally enhanced by engine-level enhancer (less strict in this case)
            result.recognition_metadata[RecognizerResult.IS_SCORE_ENHANCED_BY_CONTEXT_KEY] = True

            # Check if recognized entity has attached preposition
            if self.__has_attached_preposition_midsentense(text=text, result_start=result.start):
                sentence_part = self.__extract_sentence_part_preceding_result(
                    nlp_artifacts=nlp_artifacts, result_start=result.start
                )

                if sentence_part != "":
                    supportive_context = self.__find_supportive_context_in_sentence(
                        sentence=sentence_part
                    )
                    if supportive_context:
                        result.score += self.context_enhancement_factor

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
            adjusted_score = result.score + (overlap_ratio * self.location_overlap_factor )
            if adjusted_score != result.score:
                result.score = adjusted_score
                result.analysis_explanation.set_improved_score(adjusted_score)
                result.analysis_explanation.append_textual_explanation_line("NLP-LOC-enhanced;")

        return results

    @staticmethod
    def __extract_sentence_part_preceding_result(nlp_artifacts: NlpArtifacts, result_start: int) -> str:
        """
        Extracting the sentence which contains the start position of recognized entity using sentences from nlp_artifacts
        :param nlp_artifacts: An abstraction layer which holds different
                              items which are the result of a NLP pipeline
                              execution on a given text
        :param result_start: The start index of the entity in the original text
        :return: sentence part string from sentence start till recognized entity start
        """
        for sent in nlp_artifacts.tokens.sents:
            if (result_start >= sent.start_char) & (result_start <= sent.end_char):
                return sent.text[:result_start - sent.start_char]
        return ''

    def __find_supportive_context_in_sentence(self, sentence: str) -> str:
        """
        Extract one or more supportive context words in sentence string
        :param sentence: sentence part string
        :return: supportive context string recognized
        """
        # Sanity
        if not self.context_recognizer:
            return None

        contexts = self.context_recognizer(sentence)
        return ";".join([sentence[cont[0]:cont[0]+cont[1]] for cont in contexts]) if contexts else None

    def __has_attached_preposition_midsentense(self, text, result_start) -> bool:
        """
        Evaluate if the entity does not start the sentence and contains a preposition from the allowed list
        :param text: The actual text that was analyzed
        :param result_start: The start index of the entity in the original text
        :return: True/False flag
        """
        if (result_start >= 2) and self.allowed_prepositions:
            if (text[result_start - 1] in self.allowed_prepositions) and (re.match(r"\W", text[result_start - 2])):
                return True
        return False
