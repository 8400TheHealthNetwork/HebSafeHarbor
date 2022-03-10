import re
from typing import List

from presidio_analyzer import RecognizerResult

from hebsafeharbor import Doc
from hebsafeharbor.identifier.consolidation.consolidation_config import ENTITY_TYPES_TO_IGNORE, \
    ENTITY_TYPES_TO_POSTPROCESS, ENTITY_TYPE_TO_CATEGORY
from hebsafeharbor.common.date_utils import is_float, is_day_of_week, is_season, is_short_date


class FilterEntities:
    ENGLISH_LETTER_REGEX = re.compile(r"[a-z]|[A-z]")
    ALPHA_NUMERIC_REGEX = re.compile(r"[a-z]|[A-z]|[א-ת]|\d")
    ITEMIZED_REGEX = re.compile(r"[א-ת](\.|'|-)")

    @staticmethod
    def __call__(recognized_entities: List[RecognizerResult], doc: Doc) -> List[RecognizerResult]:
        """
        filters recognized entities that are not satisfy some initial requirements and therefore should not be
        considered as part of the consolidation:
        1. remove entities from irrelevant types
        2. filter out ORG and NAME entities that contains at least one English letter
        3. filter out only symbols entities
        4. filter out Hebrew itemized
        5. filter out DATE entities that are float number

        :param recognized_entities: list of recognized entities
        :param doc: Doc object
        :return an updated list of recognized entities after filtering
        """
        # filter out entities from irrelevant types
        filtered_entities = list(filter(
            lambda entity: entity.entity_type not in ENTITY_TYPES_TO_IGNORE.union(ENTITY_TYPES_TO_POSTPROCESS),
            recognized_entities))

        # filter out ORG and NAME entities that contains at least one English letter
        filtered_entities = list(
            filter(lambda entity: ENTITY_TYPE_TO_CATEGORY[entity.entity_type] not in ["ORG", "NAME"]
                                  or FilterEntities.ENGLISH_LETTER_REGEX.search(
                doc.text[entity.start:entity.end]) is None, filtered_entities))

        # filter out only symbols entities (doesn't contain at least one of the follows: English letter, Hebrew letter
        # or digit

        filtered_entities = list(filter(
            lambda entity: FilterEntities.ALPHA_NUMERIC_REGEX.search(doc.text[entity.start:entity.end]) is not None,
            filtered_entities))

        # filter out Hebrew itemized entities (length of 2 + match ITEMIZED_REGEX)
        filtered_entities = list(filter(lambda entity: not (
                    entity.end - entity.start == 2 and FilterEntities.ITEMIZED_REGEX.search(
                doc.text[entity.start:entity.end]) is not None), filtered_entities))

        # filter out DATE entities that are:
        # float number
        # missing a component (mm/yy, dd/mm etc.)
        # days of the week
        # seasons
        result_entities = []
        for entity in filtered_entities:
            if (ENTITY_TYPE_TO_CATEGORY[entity.entity_type] != "DATE") and (ENTITY_TYPE_TO_CATEGORY[entity.entity_type] != "TIME"):
                result_entities.append(entity)
            else:
                entity_text = doc.text[entity.start:entity.end]
                if is_float(entity_text) or is_short_date(entity_text) or is_day_of_week(entity_text) or is_season(entity_text):
                    continue
                result_entities.append(entity)

                
        filtered_entities = sorted(result_entities, key=lambda entity: (entity.start, entity.end))
        return filtered_entities

