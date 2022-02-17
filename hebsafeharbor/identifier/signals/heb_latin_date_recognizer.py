from typing import Optional

from presidio_analyzer import PatternRecognizer, Pattern
from hebsafeharbor.common.date_regex import LATIN_DATE_REGEX



class HebLatinDateRecognizer(PatternRecognizer):
    """
    A class which extends the PatternRecognizer (@Presidio) and recognizes dates that contain the name of the month
    (ינואר 1999 9)
    """    
    
    PATTERNS = [
        Pattern(
            "day month year",
            LATIN_DATE_REGEX,
            0.6
        ),                
    ]

    SUPPORTED_ENTITY = "DATE"
    
    def __init__(self):
        """
        Initializes the IdRecognizer object
        """
        super().__init__(supported_entity=HebLatinDateRecognizer.SUPPORTED_ENTITY,
                         patterns=HebLatinDateRecognizer.PATTERNS, name="HebLatinDateRecognizer",                         
                         supported_language="he"
                         )

    