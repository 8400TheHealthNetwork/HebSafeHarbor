from typing import List, Dict, Set

from presidio_analyzer import RecognizerResult

from hebsafeharbor import Doc
from hebsafeharbor.common.prepositions import DISEASE_PREPOSITIONS, MEDICATION_PREPOSITIONS, MEDICAL_TEST_PREPOSITIONS
from hebsafeharbor.common.terms_recognizer import TermsRecognizer
from hebsafeharbor.identifier.consolidation.consolidation_config import CATEGORY_TO_CONTEXT_PHRASES, \
    ENTITY_TYPE_TO_CATEGORY
from hebsafeharbor.identifier.consolidation.post_consolidation.post_consolidator_rule import PostConsolidatorRule
from hebsafeharbor.lexicons.healthcare_professional import HEALTHCARE_PROFESSIONAL


class MedicalPostConsolidator(PostConsolidatorRule):
    """
    This post processor make sure that medication or disease won't be wrongly recognized as PHI entity
    """

    MEDICAL_PHRASE_WINDOW_SIZE = 15
    HEALTHCATRE_PROFESSIONAL_WINDOW_SIZE = 5

    def __init__(self):
        """
        Initializes MedicalPostConsolidator
        """
        super().__init__(supported_entity_types=["DISEASE", "MEDICATION", "MEDICAL_TEST"],
                         lower_preference_entity_types=["PERS", "PER", "ORG", "FAC"],
                         prefer_other_types=False)

        self.medical_prepositions = set(DISEASE_PREPOSITIONS + MEDICATION_PREPOSITIONS + MEDICAL_TEST_PREPOSITIONS)

    def __call__(self, consolidated_entities: List[RecognizerResult], custom_entities: List[RecognizerResult],
                 doc: Doc) -> List[RecognizerResult]:

        """
        This method resolves overlap that can occur between diseases and medication with NAME and ORG entities.
        In case of conflict the NAME/ORG entities are removed (ignored)

        :param consolidated_entities: list of recognized entities after consolidation (no overlaps exist)
        :param custom_entities: list of recognized medical entities
        :param doc: document which stores the recognized entities
        """

        post_consolidated_entities = consolidated_entities
        if len(custom_entities) > 0:
            post_consolidated_entities = self.remove_entity_overlap_with_medical(custom_entities,
                                                                                 post_consolidated_entities, doc)

        post_consolidated_entities = self.infer_by_context(doc, post_consolidated_entities)
        post_consolidated_entities = self.remove_person_not_in_beginning(doc, post_consolidated_entities)

        return post_consolidated_entities

    def remove_entity_overlap_with_medical(self, medical_entities: List[RecognizerResult],
                                           consolidated_entities: List[RecognizerResult], doc: Doc) \
            -> List[RecognizerResult]:
        """
        Removes ORG and NAME entities that overlap with medical entities

        :param medical_entities: recognized medical entities
        :param consolidated_entities: entities after consolidation
        :param doc: Doc object
        :return: updated list of consolidated entities
        """
        no_overlap_entities = []
        offset_to_medical_entity = MedicalPostConsolidator.map_offset_to_entity(medical_entities)
        for entity in consolidated_entities:
            if entity.entity_type in self.lower_preference_entity_types:
                overlapping_medical_entities = MedicalPostConsolidator.get_entities_in_span(offset_to_medical_entity,
                                                                                            entity.start, entity.end)
                if len(overlapping_medical_entities) == 0 or not any(
                        self.is_medical_entity_contains_entity(entity, medical_entity) or
                        self.is_full_overlap(entity, medical_entity, doc) for
                        medical_entity in overlapping_medical_entities):
                    no_overlap_entities.append(entity)
            else:
                no_overlap_entities.append(entity)
        return no_overlap_entities

    def is_full_overlap(self, entity: RecognizerResult, medical_entity: RecognizerResult, doc: Doc) -> bool:
        """
        Checks if the medical entity fully overlap the given entity where full overlap means originally same boundaries
        or same boundaries when illuminating the preposition

        :param entity: the entity to check whether it overlaps with the given medical entity
        :param medical_entity: the medical entity to check whether it overlaps with the given entity
        :param doc: Doc object
        :return: True if the medical entity fully overlaps the given entity and False otherwise
        """
        if medical_entity.end == entity.end and medical_entity.start == entity.start:
            return True
        if medical_entity.end == entity.end and medical_entity.start - 1 == entity.start and doc.text[
            medical_entity.start - 1] in self.medical_prepositions:
            return True
        return False

    def is_medical_entity_contains_entity(self, entity: RecognizerResult, medical_entity: RecognizerResult) -> bool:
        """
        Checks if the medical entity contains the given entity

        :param entity: the entity to check whether the medical entity contains it
        :param medical_entity: the medical entity to check whether it contains the given entity
        :return: True if the medical entity contains the given entity and False otherwise
        """
        return entity.start >= medical_entity.start and entity.end <= medical_entity.end

    @staticmethod
    def map_offset_to_entity(entities: List[RecognizerResult]) -> Dict[int, RecognizerResult]:
        """
        Creates a mapping of an offset to the entity in this offset. Note that if an offset is not part of any entity it
        won't be part of the mapping

        :param entities: list of entities to map
        :return: a mapping of an offset to the entity in this offset, if an offset is not part of any entity it won't be
        part of the mapping
        """
        offset_to_entity = {}
        for entity in entities:
            for i in range(entity.start, entity.end):
                offset_to_entity[i] = entity
        return offset_to_entity

    @staticmethod
    def get_entities_in_span(offset_to_entity: Dict[int, RecognizerResult], start: int, end: int) -> Set[
        RecognizerResult]:
        """
        Based on the given offset to entity mapping, returns the entities exist in the given span boundaries

        :param offset_to_entity: a mapping of an offset to the entity in this offset
        :param start: span's start offset
        :param end: span's end offset
        :return: entities within the span
        """
        entities = []
        for i in range(start, end):
            if i in offset_to_entity:
                entities.append(offset_to_entity[i])
        return set(entities)

    def infer_by_context(self, doc: Doc, consolidated_entities: List[RecognizerResult]) -> List[RecognizerResult]:
        """
        Removes ORG and NAME entities in case that they follow at least one medical context phrase in specific window
        size

        :param doc: Doc object
        :param consolidated_entities: recognized entities
        :return: updated list of consolidated entities
        """
        medical_rec = TermsRecognizer(CATEGORY_TO_CONTEXT_PHRASES["MEDICAL"])
        offsets = medical_rec(doc.text, list(self.medical_prepositions))
        end_offsets = list(map(lambda offset: offset[0] + offset[1] - 1, offsets))
        res = []
        for entity in consolidated_entities:
            if entity.entity_type in self.lower_preference_entity_types:
                preceding = list(filter(lambda offset: offset < entity.start, end_offsets))
                if not any(
                        entity.start - end_offset <= MedicalPostConsolidator.MEDICAL_PHRASE_WINDOW_SIZE for end_offset
                        in preceding):
                    res.append(entity)
            else:
                res.append(entity)
        return res

    def remove_person_not_in_beginning(self, doc: Doc, consolidated_entities: List[RecognizerResult]) -> List[
        RecognizerResult]:
        """
        Removes NAME entities in case that they don't appear in the first 20% of the document and there isn't at least
        one healthcare professional phrase that precedes them (in specific window size)

        :param doc: Doc object
        :param consolidated_entities: recognized entities
        :return: updated list of consolidated entities
        """
        healthcare_professional_rec = TermsRecognizer(HEALTHCARE_PROFESSIONAL)
        offsets = healthcare_professional_rec(doc.text, list(self.medical_prepositions))
        end_offsets = list(map(lambda offset: offset[0] + offset[1] - 1, offsets))
        res = []
        for entity in consolidated_entities:
            if ENTITY_TYPE_TO_CATEGORY[entity.entity_type] == "NAME":
                if entity.start >= int(0.2 * len(doc.text)):
                    preceding = list(filter(lambda offset: offset < entity.start, end_offsets))
                    if any(entity.start - end_offset <= MedicalPostConsolidator.HEALTHCATRE_PROFESSIONAL_WINDOW_SIZE for
                           end_offset in preceding):
                        res.append(entity)
                else:
                    res.append(entity)
            else:
                res.append(entity)
        return res
