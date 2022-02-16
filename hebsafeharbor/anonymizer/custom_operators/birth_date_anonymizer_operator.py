from datetime import date
from typing import Dict

from presidio_anonymizer.operators import OperatorType, Operator

from hebsafeharbor.anonymizer.setting import DAY_MASK, MONTH_MASK, YEAR_MASK
from hebsafeharbor.common.date_utils import extract_date_components, DateMention
import re

class BirthDateAnonymizerOperator(Operator):
    """
    An instance of the DateAnonymizerOperator which extends the Operator abstract class (@Presidio). For each recognized
    entity of type BIRTH_DATE, this custom operator anonymizes the day and the month.
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

        delta = BirthDateAnonymizerOperator.calculate_estimated_age(date_container)
        above_89 = delta.days / 365.0 >= 89
        less_than_year = delta.days < 365

        # masking
        if date_container.day and date_container.day.text:
            date_container.day.text = DAY_MASK
        if date_container.month and date_container.month.text:
            date_container.month.text = MONTH_MASK if not less_than_year else date_container.month.text
        if date_container.year and date_container.year.text:
            date_container.year.text = YEAR_MASK if above_89 else date_container.year.text
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

        return "replace_day_month"

    def operator_type(self) -> OperatorType:
        """
        Returns the operator type

        :return: the operator type
        """

        return OperatorType.Anonymize

    @staticmethod
    def calculate_estimated_age(date_mention: DateMention) -> int:
        """
        Helper function that calculates estimated age of the patient based on the difference between the given birth
        date and date of today.
        The function only supprts numerical dates. For other type of date formats (Hebrew or Latin) it will return a default of 50

        :param date_mention: the mention of the birth date
        :return: the estimated age of the patient
        """
        
        current_date = date.today()
        
        if (date_mention.month.text.isdigit()) and (date_mention.day.text.isdigit()) and (date_mention.year.text.isdigit()):
            # Year treatment: if given a 4 digits year (e.g 1996), use it as is
            # for 2 digit years (i.e 96), the century will be determined using the following rule:
            # if the number formed by the last two digits of the current year >= the given year, 
            # assign the current century. otherwise, assign the previous century
            if len(date_mention.year.text) == 4:
                int_year = int(date_mention.year.text)
            elif int(date_mention.year.text) <= int(str(current_date.year)[-2:]):
                int_year =  round(current_date.year,-2) + int(date_mention.year.text)
            else:
                int_year =  round(current_date.year,-2) - 100 + int(date_mention.year.text)

            birth_date = date(int_year, int(date_mention.month.text), int(date_mention.day.text))
        else:
            birth_date =  date(date.today().year-50, date.today().month,date.today().day)

        delta = current_date - birth_date
        return delta
