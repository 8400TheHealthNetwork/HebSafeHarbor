from abc import ABC, abstractmethod
from typing import List

from presidio_analyzer import RecognizerResult

from hebsafeharbor import Doc
from hebsafeharbor.identifier.consolidation.consolidation_config import ENTITY_TYPE_TO_CATEGORY


class PostConsolidatorRule(ABC):
    """
    Entity consolidator component responsible for consolidating recognized entities after general consolidation is
    completed. This abstract class defines the methods that each consolidator must support.
    """

    def __init__(self, supported_entity_types: List[str] = list(), higher_preference_entity_types: List[str] = list(),
                 lower_preference_entity_types: List[str] = list(), prefer_other_types: bool = False):
        """
        Initializes CustomConsolidator

        :param supported_entity_types: a list of entity types that the entity consolidator supports
        :param higher_preference_entity_types: a list of entity types that are given more preference than supported
        :param lower_preference_entity_types: a list of entity types that are given less preference than supported
        :param prefer_other_types: a flag that determines how to treat entities not specified above (True - give more
        preference, False - give less preference)
        """
        self.supported_entity_types = supported_entity_types
        self.higher_preference_entity_types = higher_preference_entity_types
        self.lower_preference_entity_types = lower_preference_entity_types
        self.prefer_other_types = prefer_other_types

        self.prioritized_entity_types = self.prioritize_entity_types()

    @abstractmethod
    def __call__(self, consolidated_entities: List[RecognizerResult], custom_entities: List[RecognizerResult],
                 doc: Doc) -> List[RecognizerResult]:
        """
        This method consolidates overlap between entities of supported entity types.
        This method must be implemented by any CustomEntityConsolidator.

        :param consolidated_entities: list of entities that are consolidated so far
        :param custom_entities: full list of supported_entity_types recognized entities
        """
        pass

    def sort_entities_by_offset_start(self, entities_list: List[RecognizerResult]) -> List[RecognizerResult]:
        """
        This method extracts the recognized entities that the entity consolidator supports according to their type

        :param doc: list of the recognized entities so far
        :return list of recognized entities from the type that the entity consolidator supports
        """
        return sorted(entities_list, key=lambda entity: (entity.start, entity.end))

    def prioritize_entity_types(self) -> List[str]:
        """
        This method extracts the recognized entities that the entity consolidator supports according to their type

        :param doc: list of the recognized entities so far
        :return list of recognized entities from the type that the entity consolidator supports
        """

        # Create a list where all the entities are prioritized according to the settings
        prioritized_entity_list = self.higher_preference_entity_types + self.supported_entity_types +\
                                       self.lower_preference_entity_types
        # Check if there are entity types that aren't specified in __init__
        other_entity_types = list(set(ENTITY_TYPE_TO_CATEGORY.keys()) - set(prioritized_entity_list))
        if self.prefer_other_types:
            prioritized_entity_list = other_entity_types + prioritized_entity_list
        else:
            prioritized_entity_list = prioritized_entity_list + other_entity_types

        return prioritized_entity_list