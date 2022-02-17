from presidio_analyzer import PatternRecognizer, Pattern


class GeneralIdRecognizer(PatternRecognizer):
    """
    A class which extends the PatternRecognizer (@Presidio) and responsible for the recognition of IDs.
    """

    PATTERNS = [
        Pattern(
            "five or more digits optionally separated by dash",
            r"(\d[-]?){4,}\d",
            0.6)
    ]

    SUPPORTED_ENTITY = "ID"

    def __init__(self):
        """
        Initializes the GeneralIdRecognizer object
        """
        super().__init__(supported_entity=GeneralIdRecognizer.SUPPORTED_ENTITY, patterns=GeneralIdRecognizer.PATTERNS,
                         name="GeneralIdRecognizer", supported_language="he")
