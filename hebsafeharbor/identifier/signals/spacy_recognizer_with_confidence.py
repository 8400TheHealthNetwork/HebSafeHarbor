import logging
from collections import Set
from typing import Tuple

from presidio_analyzer import RecognizerResult
from presidio_analyzer.predefined_recognizers import SpacyRecognizer


class SpacyRecognizerWithConfidence(SpacyRecognizer):
    """
    Wrapper on SpacyRecognizer which outputs confidence scores, if provided.
    Confidence scores should be an extension of the spaCy Span object, e.g. ent._.confidence_score.
    """

    def analyze(self, text, entities, nlp_artifacts=None):
        results = []
        ner_entities = nlp_artifacts.entities

        for entity in entities:
            if entity not in self.supported_entities:
                continue
            for ent in ner_entities:
                if not self.__check_label(entity, ent.label_, self.check_label_groups):
                    continue
                if not ent.has_extension("confidence_score"):
                    raise ValueError(
                        f"confidence score not available as a spaCy span extension "
                        f"(ent._.confidence_score)"
                    )

                confidence_score = ent._.confidence_score
                textual_explanation = self.DEFAULT_EXPLANATION.format(ent.label_)

                explanation = self.build_spacy_explanation(
                    original_score=confidence_score,
                    explanation=textual_explanation,
                )

                spacy_result = RecognizerResult(
                    entity,
                    ent.start_char,
                    ent.end_char,
                    confidence_score,
                    explanation,
                )
                results.append(spacy_result)

        return results

    @staticmethod
    def __check_label(
        entity: str, label: str, check_label_groups: Tuple[Set, Set]
    ) -> bool:
        """
        Check whether the entity (from Presidio) matches the label (from spaCy).
        :param entity: Entity name
        :param label: Token label
        :param check_label_groups: A tuple of sets of names for matching

        """
        return any(
            [entity in egrp and label in lgrp for egrp, lgrp in check_label_groups]
        )
