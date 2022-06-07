from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Set

from presidio_analyzer import RecognizerResult

from hebsafeharbor import Doc
from hebsafeharbor.identifier.consolidation.consolidation_config import ENTITY_TYPE_TO_CATEGORY
from hebsafeharbor.identifier.consolidation.overlap_resolver import PreferLongestEntity, ContextBasedResolver, \
    CategoryMajorityResolver


class ConflictHandler(ABC):

    @abstractmethod
    def handle(self, entities: List[RecognizerResult], doc: Doc) -> List[RecognizerResult]:
        """
        This function handles with the conflict by triggering the right conflict resolvers based on the conflict case

        :param entities: a group of overlapped entities
        :param doc: Doc object
        :return: the entities to be kept
        """
        pass


class ExactMatch(ConflictHandler):

    def handle(self, entities: List[RecognizerResult], doc: Doc) -> List[RecognizerResult]:
        """
        This function handles with conflict in which all the entities are from the same category and have the same
        boundaries

        :param entities: a group of overlapped entities
        :param doc: Doc object
        :return: the entities to be kept
        """
        # there is no real conflict here - return the first in the given entities list
        return [entities[0]]


class SameCategory(ConflictHandler):

    def __init__(self, prefer_longest_entity_resolver: PreferLongestEntity):
        self.prefer_longest_entity_resolver = prefer_longest_entity_resolver

    def handle(self, entities: List[RecognizerResult], doc: Doc) -> List[RecognizerResult]:
        """
        This function handles with conflict in which all the entities are from the same category but have different
        boundaries

        :param entities: a group of overlapped entities
        :param doc: Doc object
        :return: the entities to be kept
        """

        # in case of prediction by NoisyDateRecognizer, prefer it
        noisy_date_entities = list(
            filter(lambda entity: entity.analysis_explanation.recognizer == "NoisyDateRecognizer", entities))
        if len(noisy_date_entities) > 0:
            return [noisy_date_entities[0]]
        # in this case we will prefer the longest entity
        return self.prefer_longest_entity_resolver(entities, doc)


class SameBoundaries(ConflictHandler):

    def __init__(self, prefer_longest_entity_resolver: PreferLongestEntity,
                 context_based_resolver: ContextBasedResolver, category_majority_resolver: CategoryMajorityResolver):
        self.prefer_longest_entity_resolver = prefer_longest_entity_resolver
        self.context_based_resolver = context_based_resolver
        self.category_majority_resolver = category_majority_resolver

    def handle(self, entities: List[RecognizerResult], doc: Doc) -> List[RecognizerResult]:
        """
        This function handles with conflict in which all the entities have the same boundaries but are from different
        categories

        :param entities: a group of overlapped entities
        :param doc: Doc object
        :return: the entities to be kept
        """

        # If there are more than one recognizers, remove the results coming out of the Hebspacy recognizer
        group_recognizers = set(map(lambda entity: entity.analysis_explanation.recognizer, entities))

        if (len(group_recognizers) > 1) and ("SpacyRecognizerWithConfidence" in group_recognizers):
            filtered_entities = []
            for entity in entities:
                if entity.analysis_explanation.recognizer != "SpacyRecognizerWithConfidence":
                    filtered_entities.append(entity)
            entities = filtered_entities

        group_categories = set(map(lambda entity: ENTITY_TYPE_TO_CATEGORY[entity.entity_type], entities))

        # currently if there are more than 2 categories we take the longest entity
        if len(group_categories) > 2:
            return self.prefer_longest_entity_resolver(entities, doc)

        if self.is_conflict_between(["ID", "CONTACT"], group_categories):
            return self.context_based_resolver(entities, doc)

        if self.is_conflict_between(["ID", "DATE"], group_categories):
            if len(entities) > 2:
                return self.category_majority_resolver(entities, doc)
            else:
                date_entity = entities[0] if ENTITY_TYPE_TO_CATEGORY[entities[0].entity_type] == "DATE" else entities[1]
                id_entity = entities[0] if ENTITY_TYPE_TO_CATEGORY[entities[0].entity_type] == "ID" else entities[1]
                # select the id entity in case that:
                # 1. the id entity is a valid Israeli ID (checksum) **OR**
                # 2. date entity was recognized by SpacyRecognizer and it is not a number
                if id_entity.analysis_explanation.validation_result or (
                        date_entity.analysis_explanation.recognizer == "SpacyRecognizerWithConfidence" and not doc.text[
                                                                                                               date_entity.start:date_entity.end].isnumeric()):
                    return [id_entity]
                else:
                    return [date_entity]

        if self.is_conflict_between(["CONTACT", "DATE"], group_categories):
            if len(entities) > 2:
                return self.category_majority_resolver(entities, doc)
            else:
                date_entity = entities[0] if ENTITY_TYPE_TO_CATEGORY[entities[0].entity_type] == "DATE" else entities[1]
                contact_entity = entities[0] if ENTITY_TYPE_TO_CATEGORY[entities[0].entity_type] == "CONTACT" else \
                    entities[1]
                # select the contact entity in case that the date entity recognized by SpacyRecognizer
                if date_entity.analysis_explanation.recognizer == "SpacyRecognizerWithConfidence":
                    return [contact_entity]
                else:
                    return [date_entity]

        if self.is_conflict_between(["CONTACT", "ORG"], group_categories):
            if len(entities) > 2:
                return self.category_majority_resolver(entities, doc)
            else:
                # select the first CONTACT entity
                for entity in entities:
                    if ENTITY_TYPE_TO_CATEGORY[entity.entity_type] == "CONTACT":
                        return [entity]

        # default - take longest
        return self.prefer_longest_entity_resolver(entities, doc)

    def is_conflict_between(self, case: List[str], condition_categories: Set[str]) -> bool:
        """
        Helper function for identifying the whose are the categories in conflict

        :param case: a list of categories that describe the case in question
        :param condition_categories: the entities' categories in the current condition
        :return: True if this is the case and False otherwise
        """
        for category in condition_categories:
            if category not in case:
                return False
        return True


class Mixed(ConflictHandler):
    def __init__(self, prefer_longest_entity_resolver: PreferLongestEntity):
        self.prefer_longest_entity_resolver = prefer_longest_entity_resolver

    def handle(self, entities: List[RecognizerResult], doc: Doc) -> List[RecognizerResult]:
        """
        This function handles with conflict in which entities are from different categories and have different
        boundaries

        :param entities: a group of overlapped entities
        :param doc: Doc object
        :return: the entities to be kept
        """

        # if the case is where the entities in conflict are one entity that contains the other we want to split it tp
        # two entities
        entity_boundaries_to_entity = defaultdict(set)
        longest_entity_start, longest_entity_end = 0, 0
        for entity in entities:
            entity_boundaries_to_entity[(entity.start, entity.end)].add(entity)
            if entity.end - entity.start > longest_entity_end - longest_entity_start:
                longest_entity_start, longest_entity_end = entity.start, entity.end

        # if there are more than 2 entities with different boundaries or there is not only one longest entity, prefer
        # the longest
        if len(entity_boundaries_to_entity.keys()) > 2 or len(
                entity_boundaries_to_entity[(longest_entity_start, longest_entity_end)]) > 1:
            return self.prefer_longest_entity_resolver(entities, doc)

        # look for entity that is contained by the longest entity and that is next to one of its boundaries (start or
        # end) and then split the longest entity into two entities according to it
        longest_entity = list(entity_boundaries_to_entity[longest_entity_start, longest_entity_end])[0]
        for entity in entities:
            if entity not in entity_boundaries_to_entity[longest_entity_start, longest_entity_end]:
                if entity.start == longest_entity_start:
                    return [RecognizerResult(entity.entity_type, entity.start, entity.end, entity.score,
                                             entity.analysis_explanation, entity.recognition_metadata),
                            RecognizerResult(longest_entity.entity_type, entity.end, longest_entity.end,
                                             longest_entity.score, longest_entity.analysis_explanation,
                                             longest_entity.recognition_metadata)]
                elif entity.end == longest_entity_end:
                    return [RecognizerResult(longest_entity.entity_type, longest_entity.start, entity.start,
                                             longest_entity.score, longest_entity.analysis_explanation,
                                             longest_entity.recognition_metadata),
                            RecognizerResult(entity.entity_type, entity.start, entity.end, entity.score,
                                             entity.analysis_explanation, entity.analysis_explanation)]
                # if the entity is not tight to one of the boundaries just prefer the longest entity
                else:
                    return self.prefer_longest_entity_resolver(entities, doc)
