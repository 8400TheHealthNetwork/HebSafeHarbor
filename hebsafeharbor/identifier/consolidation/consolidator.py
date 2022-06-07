import copy
from typing import List

from presidio_analyzer import RecognizerResult

from hebsafeharbor.common.document import Doc
from hebsafeharbor.identifier.consolidation.conflict_handler import ExactMatch, SameCategory, SameBoundaries, Mixed
from hebsafeharbor.identifier.consolidation.consolidation_config import ENTITY_TYPE_TO_CATEGORY, ConflictCase
from hebsafeharbor.identifier.consolidation.filter_entities import FilterEntities
from hebsafeharbor.identifier.consolidation.post_consolidation.city_country_post_consolidator import \
    CityCountryPostConsolidator
from hebsafeharbor.identifier.consolidation.overlap_resolver import PreferLongestEntity, ContextBasedResolver, \
    CategoryMajorityResolver
from hebsafeharbor.identifier.consolidation.post_consolidation.medical_post_consolidator import MedicalPostConsolidator


class NerConsolidator:
    """
    A class which is responsible for consolidating the entities recognized by the different signals to create a set of
    entities without overlaps. It applies custom policy for prioritizing the results of the different signals.
    """

    def __init__(self):
        self.filter_entities = FilterEntities()
        self.prefer_longest_entity_resolver = PreferLongestEntity()
        self.context_based_resolver = ContextBasedResolver()
        self.category_majority_resolver = CategoryMajorityResolver()
        self.conflict_handlers = {
            ConflictCase.EXACT_MATCH: ExactMatch(),
            ConflictCase.SAME_CATEGORY: SameCategory(self.prefer_longest_entity_resolver),
            ConflictCase.SAME_BOUNDARIES: SameBoundaries(self.prefer_longest_entity_resolver,
                                                         self.context_based_resolver,
                                                         self.category_majority_resolver),
            ConflictCase.MIXED: Mixed(self.prefer_longest_entity_resolver)
        }
        self.postprocess_consolidators = [CityCountryPostConsolidator(), MedicalPostConsolidator()]

    def __call__(self, doc: Doc) -> Doc:
        """
        :param doc: a Doc object which contains the entities recognized by the different signals
        :return: an updated Doc object that contains the consolidated entities (a set of entities with no overlaps)
        """

        recognized_entities = copy.deepcopy(doc.smoothed_entities)
        filtered_entities = self.filter_entities(recognized_entities, doc)
        group = NerConsolidator.get_next_overlapped_entities_group(filtered_entities, 0)
        consolidated_entities = []
        while len(group) > 0:
            selected_entity = self.consolidate_entities(group, doc)
            if selected_entity is None:
                # only one entity in group and it doesn't satisfy the minimal conditions
                last_entity = group[0]
            else:
                consolidated_entities += selected_entity
                last_entity = selected_entity[-1]
            group = NerConsolidator.get_next_overlapped_entities_group(filtered_entities, last_entity.end)

        # trigger the custom entity consolidators
        for custom_consolidator in self.postprocess_consolidators:
            custom_entities = filter(
                lambda entity: entity.entity_type in custom_consolidator.supported_entity_types,
                recognized_entities)
            if custom_entities:
                consolidated_entities = custom_consolidator(consolidated_entities, list(custom_entities), doc)

        doc.consolidated_results = consolidated_entities
        return doc

    @staticmethod
    def get_next_overlapped_entities_group(entities: List[RecognizerResult], start_offset: int) -> List[
        RecognizerResult]:
        """
        Helper function for getting the next group of overlapped entities

        :param entities: recognized entities
        :param start_offset: the offset to start the search from
        :return: the next subgroup of overlapped entities (the returned list will be empty if no entities left)
        """
        group = []
        not_yet_handled_entities = list(filter(lambda entity: entity.start >= start_offset, entities))
        if len(not_yet_handled_entities) == 0:
            return group
        not_yet_handled_entities = sorted(not_yet_handled_entities, key=lambda entity: entity.start)
        group.append(not_yet_handled_entities[0])
        min_group_offset, max_group_offset = group[0].start, group[0].end
        for entity in not_yet_handled_entities[1:]:
            if min_group_offset <= entity.start < max_group_offset:
                group.append(entity)
            else:
                return group
        return group

    @staticmethod
    def keep_single_entity(entity: RecognizerResult, doc: Doc) -> bool:
        """
        Helper function which decides whether to keep an entity that doesn't overlap any other recognized entity

        :param entity: an entity that doesn't overlap any other recognized entity
        :param doc: Doc object
        :return True if the entity should be kept and False otherwise
        """
        entity_text = doc.text[entity.start: entity.end]
        # don't keep entity if entity text contains only one character
        if len(entity_text) < 2:
            return False
        # don't keep entity in case it is in English and all caps
        if 'A' <= entity_text[0] <= 'Z' and entity_text.isalpha() and entity_text.upper() == entity_text:
            return False
        return True

    def consolidate_entities(self, entities_in_conflict: List[RecognizerResult], doc: Doc) -> List[RecognizerResult]:
        """
        This method consolidate a group of overlapped entities by identifying the conflict case and triggering the
        relevant condition handler for resolution

        :param entities_in_conflict: group of overlapped entities
        :param doc: Doc object
        :return: the list of selected entities out of the group or None in case it doesn't satisfy the minimal
        requirements
        """

        # if there is only one entity in group there is no conflict - keep it in case it satisfying the minimal
        # requirements
        if len(entities_in_conflict) == 1:
            if NerConsolidator.keep_single_entity(entities_in_conflict[0], doc):
                return entities_in_conflict
            else:
                return None

        conflict_case = NerConsolidator.infer_conflict_case(entities_in_conflict)
        return self.conflict_handlers[conflict_case].handle(entities_in_conflict, doc)

    @staticmethod
    def infer_conflict_case(entities_in_conflict: List[RecognizerResult]) -> ConflictCase:
        """
        Determines the consolidation conflict case (same categories, same boundaries, etc.)

        :param entities_in_conflict: group of entities with overlaps
        :return conflict case
        """
        group_categories = set(map(lambda entity: ENTITY_TYPE_TO_CATEGORY[entity.entity_type], entities_in_conflict))
        same_category = len(group_categories) == 1
        group_start_offsets = set(map(lambda entity: entity.start, entities_in_conflict))
        group_end_offsets = set(map(lambda entity: entity.end, entities_in_conflict))
        same_boundaries = len(group_start_offsets) == 1 & len(group_end_offsets) == 1

        if same_category & same_boundaries:
            return ConflictCase.EXACT_MATCH
        if same_category:
            return ConflictCase.SAME_CATEGORY
        if same_boundaries:
            return ConflictCase.SAME_BOUNDARIES
        return ConflictCase.MIXED
