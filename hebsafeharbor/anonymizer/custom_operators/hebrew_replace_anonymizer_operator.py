from typing import Dict

from presidio_anonymizer.operators import Operator, OperatorType

class ReplaceInHebrew(Operator):
    """
    An instance of the Operator abstract class (@Presidio). For each recognized entity ,this custom
    replace it by custom string depending on its entity type.
    """

    def operate(self, text: str = None, params: Dict = None) -> str:
        """:return: new_value."""
        entity_type = params.get("entity_type")
        if entity_type in ["PERS", "PER"]:
            return "<שם_>"
        elif entity_type in ["LOC", "GPE"]:
            return "<מיקום_>"
        elif entity_type in ["ORG", "FAC"]:
            return "<ארגון_>"
        elif entity_type in ["CREDIT_CARD", "ISRAELI_ID_NUMBER", "ID"]:
            return "<מזהה_>"
        elif entity_type in ["EMAIL_ADDRESS", "IP_ADDRESS", "PHONE_NUMBER", "URL"]:
            return "<קשר_>"
        elif entity_type in ["DATE"]:
            return "<תאריך_>"


    def validate(self, params: Dict = None) -> None:
        """Validate the new value is string."""
        pass

    def operator_name(self) -> str:
        """Return operator name."""
        return "replace_in_hebrew"

    def operator_type(self) -> OperatorType:
        """Return operator type."""
        return OperatorType.Anonymize
