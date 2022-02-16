from abc import ABC, abstractmethod
from typing import List

from presidio_analyzer import RecognizerResult

from hebsafeharbor import Doc


class EntitySplitter(ABC):
    """
    Entity splitter component responsible for splitting recognized entities from a given type to more specific types.
    This abstract class defines the methods that each entity splitter must support.
    """

    def __init__(self, supported_entity_types: List[str]):
        """
        Initializes EntitySplitter

        :param supported_entity_types: a list of entity types that the entity splitter supports
        """
        self.supported_entity_types = supported_entity_types

    @abstractmethod
    def __call__(self, doc: Doc) -> Doc:
        """
        This method split or change the type of an entity into higher granularity. It works only on the entities of
        supported entity types. This method must be implemented by any EntitySplitter.

        :param doc: document which stores the recognized entities before and after the splitting process that was done
        so far
        """
        pass

    def filter_relevant_entities(self, doc: Doc) -> List[RecognizerResult]:
        """
        This method extracts the recognized entities that the entity splitter supports according to their type

        :param doc: documents which includes the recognized entities so far
        :return list of recognized entities from the type that the entity splitter supports
        """
        return list(
            filter(lambda entity: entity.entity_type in self.supported_entity_types, doc.granular_analyzer_results))
