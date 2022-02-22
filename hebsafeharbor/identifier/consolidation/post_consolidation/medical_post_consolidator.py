from typing import List, Dict, Set

from presidio_analyzer import RecognizerResult

from hebsafeharbor import Doc
from hebsafeharbor.common.prepositions import DISEASE_PREPOSITIONS, MEDICATION_PREPOSITIONS
from hebsafeharbor.common.terms_recognizer import TermsRecognizer
from hebsafeharbor.identifier.consolidation.consolidation_config import CATEGORY_TO_CONTEXT_PHRASES, \
    ENTITY_TYPE_TO_CATEGORY
from hebsafeharbor.identifier.consolidation.post_consolidation.post_consolidator_rule import PostConsolidatorRule


class MedicalPostConsolidator(PostConsolidatorRule):
    """
    This post processor make sure that medication or disease won't be wrongly recognized as PHI entity
    """

    def __init__(self):
        """
        Initializes MedicalPostConsolidator
        """
        super().__init__(supported_entity_types=["DISEASE", "MEDICATION"],
                         lower_preference_entity_types=["PERS", "PER", "ORG", "FAC"],
                         prefer_other_types=False)

        self.medical_prepositions = set(DISEASE_PREPOSITIONS + MEDICATION_PREPOSITIONS)

    def __call__(self, consolidated_entities: List[RecognizerResult], custom_entities: List[RecognizerResult],
                 doc: Doc) -> List[RecognizerResult]:

        """
        This method resolves overlap that can occur between diseases and medication with NAME and ORG entities.
        In case of conflict the NAME/ORG entities are removed (ignored)

        :param consolidated_entities: list of recognized entities after consolidation (no overlaps exist)
        :param custom_entities: list of recognized medical entities
        :param doc: document which stores the recognized entities
        """

        if len(custom_entities) > 0:
            post_consolidated_entities = []
            offset_to_medical_entity = MedicalPostConsolidator.map_offset_to_entity(custom_entities)
            for entity in consolidated_entities:
                if entity.entity_type in self.lower_preference_entity_types:
                    overlapping_medical_entities = MedicalPostConsolidator.get_entities_in_span(offset_to_medical_entity,
                                                                                                entity.start, entity.end)
                    if len(overlapping_medical_entities) == 0 or not any(
                            self.is_full_overlap(entity, medical_entity, doc) for medical_entity in
                            overlapping_medical_entities):
                        post_consolidated_entities.append(entity)
                else:
                    post_consolidated_entities.append(entity)
        else:
            post_consolidated_entities = consolidated_entities

        post_consolidated_entities = self.infer_by_context(doc, post_consolidated_entities)
        post_consolidated_entities = self.remove_person_not_in_beginning(doc, post_consolidated_entities)

        return post_consolidated_entities

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

    def infer_by_context(self, doc: Doc, consolidated_entities: List[RecognizerResult]):
        medical_rec = TermsRecognizer(CATEGORY_TO_CONTEXT_PHRASES["MEDICAL"])
        offsets = medical_rec(doc.text, list(self.medical_prepositions))
        end_offsets = list(map(lambda offset: offset[0] + offset[1] - 1, offsets))
        res = []
        for entity in consolidated_entities:
            if entity.entity_type in self.lower_preference_entity_types:
                preceding = list(filter(lambda offset: offset < entity.start, end_offsets))
                if not any(entity.start - end_offset <= 15 for end_offset in preceding):
                    res.append(entity)
            else:
                res.append(entity)
        return res

    def remove_person_not_in_beginning(self, doc: Doc, consolidated_entities: List[RecognizerResult]):
        healthcare_professional = ["ד\"ר", "דר", "דוקטור", "פרופסור", "פרופ\'", "פרופ", "רופא"]
        healthcare_professional_rec = TermsRecognizer(healthcare_professional)
        offsets = healthcare_professional_rec(doc.text, list(self.medical_prepositions))
        end_offsets = list(map(lambda offset: offset[0] + offset[1] - 1, offsets))
        res = []
        for entity in consolidated_entities:
            if ENTITY_TYPE_TO_CATEGORY[entity.entity_type] == "NAME":
                if entity.start >= int(0.2 * len(doc.text)):
                    preceding = list(filter(lambda offset: offset < entity.start, end_offsets))
                    if any(entity.start - end_offset <= 5 for end_offset in preceding):
                        res.append(entity)
                else:
                    res.append(entity)
            else:
                res.append(entity)
        return res
