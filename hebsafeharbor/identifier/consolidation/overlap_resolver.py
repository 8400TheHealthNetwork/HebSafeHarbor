from abc import abstractmethod, ABC
from collections import Counter
from typing import List

from presidio_analyzer import RecognizerResult

from hebsafeharbor import Doc
from hebsafeharbor.common.terms_recognizer import TermsRecognizer
from hebsafeharbor.identifier.consolidation.consolidation_config import CATEGORY_TO_CONTEXT_PHRASES, ENTITY_TYPE_TO_CATEGORY


class OverlapResolver(ABC):
    """
    This abstract class defines one method that every overlap resolver must implement - the function that resolves the
    conflict between entities.
    """

    @abstractmethod
    def __call__(self, entities_in_conflict: List[RecognizerResult], doc: Doc) -> List[RecognizerResult]:
        """
        This function resolves the conflict between overlapped entities. Given a group of overlapped entities it resolve
        the conflict (type and boundaries) and return the updated list of entities without overlaps

        :param entities_in_conflict: a group of overlapped entities
        :param doc: Doc object
        :return: the entities that should be kept (the result of the overlap resolution)
        """
        pass


class PreferLongestEntity(OverlapResolver):

    def __call__(self, entities_in_conflict: List[RecognizerResult], doc: Doc) -> List[RecognizerResult]:
        """
        This function resolves the conflict between overlapped entities by keeping only the longest entity

        :param entities_in_conflict: a group of overlapped entities
        :param doc: Doc object
        :return: list that contains the longest entity
        """
        sorted_by_length = sorted(entities_in_conflict, key=lambda entity: entity.end - entity.start, reverse=True)
        return [sorted_by_length[0]]


class ContextBasedResolver(OverlapResolver):

    def __init__(self, window_size=5):
        """
        Initializes ContextBasedResolver by creating the TermsRecognizer(s) for each of the categories

        :param window_size: context size limit (one side)
        """
        self.window_size = window_size
        self.category_to_recognizer = {}
        for category, context_phrases in CATEGORY_TO_CONTEXT_PHRASES.items():
            self.category_to_recognizer[category] = TermsRecognizer(context_phrases)

    def __call__(self, entities_in_conflict: List[RecognizerResult], doc: Doc) -> List[RecognizerResult]:
        """
        This function resolves the conflict between overlapped entities by examining words in context that may hint on
        the right category

        :param entities_in_conflict: a group of overlapped entities
        :param doc: Doc object
        :return: the entities to be kept according to the context
        """
        categories = set(map(lambda entity: ENTITY_TYPE_TO_CATEGORY[entity.entity_type], entities_in_conflict))
        category_to_offsets = {category: self.category_to_recognizer[category](doc.text) for category in categories}
        category_to_end_offsets = {}
        for category, offsets in category_to_offsets.items():
            category_to_end_offsets[category] = list(map(lambda offset: offset[0] + offset[1] - 1, offsets))

        for index, entity in enumerate(entities_in_conflict):
            entity_category = ENTITY_TYPE_TO_CATEGORY[entity.entity_type]
            preceding = list(filter(lambda offset: offset < entity.start, category_to_end_offsets[entity_category]))
            if len(preceding) > 0 and any(entity.start - end_offset <= self.window_size for end_offset in preceding):
                return [entity]

        # in case that there are no indicators in context, return the longest entity
        sort_by_length = sorted(entities_in_conflict, key=lambda entity: entity.end - entity.start, reverse=True)
        return [sort_by_length[0]]


class CategoryMajorityResolver(OverlapResolver):
    def __call__(self, entities_in_conflict: List[RecognizerResult], doc: Doc) -> List[RecognizerResult]:
        """
        This function resolves the conflict between overlapped entities based on the entities' category where the
        selected entity is from the major category

        :param entities_in_conflict: a group of overlapped entities
        :param doc: Doc object
        :return: the entities with the major category
        """
        categories = map(lambda entity: ENTITY_TYPE_TO_CATEGORY[entity.entity_type], entities_in_conflict)
        counter = Counter(categories)
        # the most common category is the first item in the first tuple in list
        most_common_category = counter.most_common(1)[0][0]
        entities_with_most_common_category = list(
            filter(lambda entity: ENTITY_TYPE_TO_CATEGORY[entity.entity_type] == most_common_category,
                   entities_in_conflict))
        return [entities_with_most_common_category[0]]
