from abc import ABC, abstractmethod
from typing import List, Set

from presidio_analyzer import RecognizerResult

from hebsafeharbor import Doc
from hebsafeharbor.identifier.consolidation.consolidation_config import ENTITY_TYPE_TO_CATEGORY
from hebsafeharbor.identifier.consolidation.overlap_resolver import PreferLongestEntity, ContextBasedResolver, \
    CategoryMajorityResolver


class ConflictHandler(ABC):

    @abstractmethod
    def handle(self, entities: List[RecognizerResult], doc: Doc) -> RecognizerResult:
        """
        This function handles with the conflict by triggering the right conflict resolvers based on the conflict case

        :param entities: a group of overlapped entities
        :param doc: Doc object
        :return: the selected entity to be kept
        """
        pass


class ExactMatch(ConflictHandler):

    def handle(self, entities: List[RecognizerResult], doc: Doc) -> RecognizerResult:
        """
        This function handles with conflict in which all the entities are from the same category and have the same
        boundaries

        :param entities: a group of overlapped entities
        :param doc: Doc object
        :return: the selected entity to be kept
        """
        # there is no real conflict here - return the first in the given entities list
        return entities[0]


class SameCategory(ConflictHandler):

    def __init__(self, prefer_longest_entity_resolver: PreferLongestEntity):
        self.prefer_longest_entity_resolver = prefer_longest_entity_resolver

    def handle(self, entities: List[RecognizerResult], doc: Doc) -> RecognizerResult:
        """
        This function handles with conflict in which all the entities are from the same category but have different
        boundaries

        :param entities: a group of overlapped entities
        :param doc: Doc object
        :return: the selected entity to be kept
        """
        # in this case we will prefer the longest entity
        return self.prefer_longest_entity_resolver(entities, doc)


class SameBoundaries(ConflictHandler):

    def __init__(self, prefer_longest_entity_resolver: PreferLongestEntity,
                 context_based_resolver: ContextBasedResolver, category_majority_resolver: CategoryMajorityResolver):
        self.prefer_longest_entity_resolver = prefer_longest_entity_resolver
        self.context_based_resolver = context_based_resolver
        self.category_majority_resolver = category_majority_resolver

    def handle(self, entities: List[RecognizerResult], doc: Doc) -> RecognizerResult:
        """
        This function handles with conflict in which all the entities have the same boundaries but are from different
        categories

        :param entities: a group of overlapped entities
        :param doc: Doc object
        :return: the selected entity to be kept
        """
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
                        date_entity.analysis_explanation.recognizer == "SpacyRecognizer" and not doc.text[
                                                                                                 date_entity.start:date_entity.end].isnumeric()):
                    return id_entity
                else:
                    return date_entity

        if self.is_conflict_between(["CONTACT", "DATE"], group_categories):
            if len(entities) > 2:
                return self.category_majority_resolver(entities, doc)
            else:
                date_entity = entities[0] if ENTITY_TYPE_TO_CATEGORY[entities[0].entity_type] == "DATE" else entities[1]
                contact_entity = entities[0] if ENTITY_TYPE_TO_CATEGORY[entities[0].entity_type] == "CONTACT" else \
                    entities[1]
                # select the contact entity in case that the date entity recognized by SpacyRecognizer
                if date_entity.analysis_explanation.recognizer == "SpacyRecognizer":
                    return contact_entity
                else:
                    return date_entity

        if self.is_conflict_between(["CONTACT", "ORG"], group_categories):
            if len(entities) > 2:
                return self.category_majority_resolver(entities, doc)
            else:
                # select the first CONTACT entity
                for entity in entities:
                    if ENTITY_TYPE_TO_CATEGORY[entity.entity_type] == "CONTACT":
                        return entity

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

    def handle(self, entities: List[RecognizerResult], doc: Doc) -> RecognizerResult:
        """
        This function handles with conflict in which entities are from different categories and have different
        boundaries

        :param entities: a group of overlapped entities
        :param doc: Doc object
        :return: the selected entity to be kept
        """
        # currently in this case we will prefer the longest entity
        return self.prefer_longest_entity_resolver(entities, doc)
