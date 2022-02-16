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

        consolidated_entities.extend(custom_entities)
        consolidated_entities = self.sort_entities_by_offset_start(consolidated_entities)

        for i in range(1, len(consolidated_entities)):
            if consolidated_entities[i].start <= consolidated_entities[i-1].end:
                if self.prioritized_entity_types.index(consolidated_entities[i].entity_type) <= \
                        self.prioritized_entity_types.index(consolidated_entities[i-1].entity_type):
                    if (consolidated_entities[i].start - consolidated_entities[i - 1].start) > 1 & (
                            consolidated_entities[i - 1].end - consolidated_entities[i].end) >= 1:
                        consolidated_entities[i].end = consolidated_entities[i].start
                    else:
                        consolidated_entities[i - 1].end = consolidated_entities[i].start
                else:
                    consolidated_entities[i].start = consolidated_entities[i - 1].end \
                        if consolidated_entities[i - 1].end <= consolidated_entities[i].end \
                        else consolidated_entities[i].end

        # .......            | ........            | ........... -> ........... | ........... -> ....******* |
        # ******* -> ******* |  ******* -> ******* |   ********                 |     *******                |

        # ******* -> ******* | ********** -> ********** | ******** -> ********| ********  -> ********..|
        # .......            |   .....                  |  .......            |  .........             |

        for entity in consolidated_entities:
            if (entity.entity_type in self.lower_preference_entity_types) | (
                    entity.entity_type in self.supported_entity_types):
                if (entity.end - entity.start) == 0:
                        consolidated_entities.remove(entity)
                if (entity.end - entity.start) == 1:
                    if doc.text[entity.start:entity.end] in self.location_prepositions:
                        consolidated_entities.remove(entity)

        return consolidated_entities