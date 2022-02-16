from typing import Dict

from presidio_anonymizer.operators import OperatorType, Operator

from hebsafeharbor.common.country_utils import COUNTRY_DICT

class CountryAnonymizerOperator(Operator):
    """
    An instance of the CountryAnonymizerOperator which extends the Operator abstract class (@Presidio). For each recognized
    entity of type COUNTRY, this custom operator anonymizes the country according to the regions mapping.
    """

    def operate(self, text: str, params: Dict = None) -> str:
        """
        This method applies the anonymization policy of the CountryAnonymizerOperator on the given recognized entity text

        :param text: recognized entity text for anonymization
        :param params: optional parameters
        :return: the anonymized text of the entity
        """

        if text in COUNTRY_DICT.keys():
            return COUNTRY_DICT[text]
        else:
            return "<מדינה_>"

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

        return "replace_by_region"

    def operator_type(self) -> OperatorType:
        """
        Returns the operator type

        :return: the operator type
        """

        return OperatorType.Anonymize
