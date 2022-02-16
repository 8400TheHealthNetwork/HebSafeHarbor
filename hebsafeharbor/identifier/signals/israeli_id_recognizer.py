from typing import Optional

from presidio_analyzer import PatternRecognizer, Pattern


class IsraeliIdNumberRecognizer(PatternRecognizer):
    """
    A class which extends the PatternRecognizer (@Presidio) and responsible for the recognition of Israeli ID number
    entity and its validation.
    """

    PATTERNS = [
        Pattern(
            "9 digits israeli id number",
            r"[0-9]{9}",
            0.6
        ),
        Pattern(
            "8 digits israeli id number (without the leading zero)",
            r"[0-9]{8}",
            0.6
        ),
        Pattern(
            "9 digits israeli id number with a dash before the check digit (the last digit)",
            r"[0-9]{8}-[0-9]",
            0.6
        ),
    ]

    SUPPORTED_ENTITY = "ISRAELI_ID_NUMBER"

    def __init__(self):
        """
        Initializes the IdRecognizer object
        """
        super().__init__(supported_entity=IsraeliIdNumberRecognizer.SUPPORTED_ENTITY,
                         patterns=IsraeliIdNumberRecognizer.PATTERNS, name="IsraeliIdNumberRecognizer",
                         supported_language="he")

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        """
        Validate the israeli id number recognized pattern by running checksum on a detected pattern (Luhn algorithm).

        :param pattern_text: the text to validated. Only the part in text that was detected by the regex engine
        :return: A bool indicating whether the validation was successful.
        """
        pattern_text = pattern_text.replace("-", "")
        if len(pattern_text) == 8:
            pattern_text = "0" + pattern_text
        check_digit = int(pattern_text[-1])
        id_digits_str = pattern_text[:-1]
        values_sum = 0
        for index, digit_char in enumerate(id_digits_str):
            digit = int(digit_char)
            if index % 2 == 1:
                digit *= 2
            if digit > 10:
                digit = int(digit / 10) + (digit % 10)
            values_sum += digit
        return 10 - (values_sum % 10) == check_digit
