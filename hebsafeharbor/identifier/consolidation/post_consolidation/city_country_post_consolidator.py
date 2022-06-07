from typing import List

from presidio_analyzer import RecognizerResult

from hebsafeharbor import Doc
from hebsafeharbor.common.prepositions import LOCATION_PREPOSITIONS
from hebsafeharbor.identifier.consolidation.post_consolidation.post_consolidator_rule import PostConsolidatorRule


class CityCountryPostConsolidator(PostConsolidatorRule):
    """
    This post consolidator decides for each CITY/COUNTRY entity whether to keep it or not and adjust overlapped entities
    if necessary.
    """

    MINIMUM_CONFIDENCE_TO_RECOGNIZE = 0.5  # if final confidence score is below - exclude from entities

    def __init__(self):
        """
        Initializes CityCountryPostConsolidator
        """
        super().__init__(supported_entity_types=["COUNTRY", "CITY"],
                         higher_preference_entity_types=["PERS", "PER", "ORG", "FAC"],
                         lower_preference_entity_types=["LOC", "GPE"],
                         prefer_other_types=False)

        self.location_prepositions = LOCATION_PREPOSITIONS

    def __call__(self, consolidated_entities: List[RecognizerResult], custom_entities: List[RecognizerResult],
                 doc: Doc) -> List[RecognizerResult]:
        """
        This method resolves overlap that can occur between entities recognized as more generic (LOC/GPE, currently
        recognized by HebSpacy) and more specific (COUNTRY/CITY, recognized using custom recognizers). Giving more
        priority to the specific ones allows more flexible anonymization.

        :param doc: document which stores the recognized entities
        """
        if len(custom_entities) == 0:
            return consolidated_entities

        candidate_entities = [entity for entity in custom_entities if
                              entity.score >= self.MINIMUM_CONFIDENCE_TO_RECOGNIZE]
        if len(candidate_entities) == 0:
            return consolidated_entities

        consolidated_entities.extend(candidate_entities)
        consolidated_entities = self.sort_entities_by_offset_start(consolidated_entities)

        prev_entity_id = 0  # to handle cases where overlap is between more than 2 entities. Ex. שרון גשר מר"ג
        # TODO: when any entity is adjusted, resort and loop over the list again (Ex. קיבוץ עין החורש)
        for cur_entity_id in range(1, len(consolidated_entities)):
            if consolidated_entities[cur_entity_id].start <= consolidated_entities[prev_entity_id].end:
                # Define which entity type has priority
                if self.prioritized_entity_types.index(consolidated_entities[cur_entity_id].entity_type) <= \
                        self.prioritized_entity_types.index(consolidated_entities[prev_entity_id].entity_type):
                    primary_entity_id = cur_entity_id
                else:
                    primary_entity_id = prev_entity_id

                # If entity is within [from both sides] longer entity - we prefer longer entity regardless of priority
                if (consolidated_entities[cur_entity_id].start - consolidated_entities[prev_entity_id].start) > 1 & (
                        consolidated_entities[prev_entity_id].end - consolidated_entities[cur_entity_id].end) >= 1:
                    consolidated_entities[cur_entity_id].end = consolidated_entities[cur_entity_id].start
                    # prev_entity_id stays the same
                # if current entity has priority, we'll adjust previous
                elif cur_entity_id == primary_entity_id:
                    consolidated_entities[prev_entity_id].end = consolidated_entities[cur_entity_id].start
                    prev_entity_id = cur_entity_id
                # if previous entity has priority, we'll adjust current
                else:
                    if consolidated_entities[prev_entity_id].end <= consolidated_entities[cur_entity_id].end:
                        consolidated_entities[cur_entity_id].start = consolidated_entities[prev_entity_id].end
                        prev_entity_id = cur_entity_id
                    else:
                        consolidated_entities[cur_entity_id].start = consolidated_entities[cur_entity_id].end
                        # prev_entity_id stays the same
            else:
                prev_entity_id = cur_entity_id

        # .......            | ........            | ........... -> ........... | ........... -> ....******* |
        # ******* -> ******* |  ******* -> ******* |   ********                 |     *******                |

        # ******* -> ******* | ********** -> ********** | ******** -> ********| ********  -> ********..|
        # .......            |   .....                  |  .......            |  .........             |

        # remove entity scraps
        for entity in reversed(consolidated_entities):
            if (entity.entity_type in self.lower_preference_entity_types) | (
                    entity.entity_type in self.supported_entity_types):
                if (entity.end - entity.start) == 0:
                    consolidated_entities.remove(entity)
                if (entity.end - entity.start) == 1:
                    if doc.text[entity.start:entity.end] in self.location_prepositions:
                        consolidated_entities.remove(entity)

        return consolidated_entities
