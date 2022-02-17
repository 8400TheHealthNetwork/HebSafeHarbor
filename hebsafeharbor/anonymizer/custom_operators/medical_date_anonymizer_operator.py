from typing import Dict

from presidio_anonymizer.operators import OperatorType, Operator

from hebsafeharbor.anonymizer.setting import DAY_MASK
from hebsafeharbor.common.date_utils import extract_date_components


class MedicalDateAnonymizerOperator(Operator):
    """
    An instance of the DateAnonymizerOperator which extends the Operator abstract class (@Presidio). For each recognized
    entity of type MEDICAL_DATE, this custom operator anonymizes the only the day.
    """

    def operate(self, text: str, params: Dict = None) -> str:
        """
        This method applies the anonymization policy of the BirthDateAnonymizerOperator on the given recognized entity text

        :param text: recognized entity text for anonymization
        :param params: optional parameters
        :return: the anonymized text of the entity
        """
        
        date_container = extract_date_components(text)
        # in case that the components extraction failed, all values will be none - returning the original text
        if date_container.day is None and date_container.month is None and date_container.year is None:
            return text

        # masking
        if date_container.day and date_container.day.text:
            date_container.day.text = DAY_MASK
        return date_container.reconstruct_date_string()

    def validate(self, params: Dict = None) -> None:
        """
        This method validates each operator parameters
        :param params: operator custom parameters
        """
        pass

    def operator_name(self) -> str:
        """
        Returns the operator name

        :return: the operator name
        """

        return "replace_only_day"

    def operator_type(self) -> OperatorType:
        """
        Returns the operator type

        :return: the operator type
        """

        return OperatorType.Anonymize
