import re
from typing import List, Callable

from presidio_analyzer import RecognizerResult

from hebsafeharbor import Doc
from hebsafeharbor.identifier.entity_smoother.entity_smoother_rule import EntitySmootherRule


class LocationsMergerRule(EntitySmootherRule):
    """
        An abstract class which represents a rule which expands some entities according to some policy. If the
        requirement it holds is satisfied, it performs some action.
        """

    MAXIMUM_ALLOWED_DISTANCE = 5

    def __init__(self):
        """
        Initializing EntityExpanderRule by defining its name and the requirement it verifies
        """
        requirement: Callable[[List[RecognizerResult], Doc], bool] = LocationsMergerRule.merging_requirement
        super().__init__("LocationsMergerRule", requirement)

    def __call__(self, doc: Doc) -> Doc:
        """
        Executes the EntityExpanderRule on a list of entities by checking if the requirement is
        satisfied and return the updated Doc object after performing some action

        :param doc: doc object
        :return an updated Doc object after executing the rule
        """
        # concentrating on entities recognized only be HebSpacy signal
        heb_spacy_entities = filter(lambda entity: entity.analysis_explanation.recognizer == "HebSpacy",
                                    doc.smoothed_entities)
        heb_spacy_entities = sorted(heb_spacy_entities, key=lambda entity: entity.start)

        entities_after_expansion = []
        i = 0
        while i + 1 < len(heb_spacy_entities):
            if self.requirement([heb_spacy_entities[i], heb_spacy_entities[i + 1]], doc):
                # merging the entities along with the number between them
                merged_entity = heb_spacy_entities[i]
                merged_entity.end = heb_spacy_entities[i + 1].end
                entities_after_expansion.append(merged_entity)
                # moving on to the next pair of entities
                i += 2
            else:
                entities_after_expansion.append(heb_spacy_entities[i])
                # the requirement is not satisfied so trying with the next entity
                i += 1
        if i < len(heb_spacy_entities):
            entities_after_expansion.append(heb_spacy_entities[i])

        # taking the entities which weren't recognized by HebSpacy along with the entities after performing the rule
        # logic
        updated_entities = list(filter(lambda entity: entity.analysis_explanation.recognizer != "HebSpacy",
                                       doc.smoothed_entities)) + entities_after_expansion
        updated_entities = sorted(updated_entities, key=lambda entity: entity.start)
        doc.smoothed_entities = updated_entities

        return doc

    @staticmethod
    def merging_requirement(entities: List[RecognizerResult], doc: Doc) -> bool:
        """
        a function which defines the requirements for entities to be merged by the LocationsMergerRule:
        - both entities must be from type LOC
        - entities cannot be far from each other
        - there is an unrecognized number between them

        :return True if all the requirements are satisfied and False otherwise
        """

        # check if both entities are from type LOC
        if entities[0].entity_type != "LOC" or entities[1].entity_type != "LOC":
            return False

        # check if the entities are not far from each other
        if entities[1].start - entities[0].end > LocationsMergerRule.MAXIMUM_ALLOWED_DISTANCE:
            return False

        # check if there is an unrecognized number between the entities
        context_start_offset = entities[0].end + 1
        context_end_offset = entities[1].start
        context = doc.text[context_start_offset:context_end_offset]
        number_regex = re.compile(r"\d+")
        if number_regex.search(context):
            return True

        return False
