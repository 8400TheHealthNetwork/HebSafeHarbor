from typing import Optional

from presidio_analyzer import PatternRecognizer, Pattern
from hebsafeharbor.common.date_regex import LATIN_DATE_REGEX,EN_DATE_REGEX



class HebLatinDateRecognizer(PatternRecognizer):
    """
    A class which extends the PatternRecognizer (@Presidio) and recognizes dates that contain the name of the month
    (ינואר 1999 9)
    """    
    
    PATTERNS = [
        Pattern(
            "dates written in Hebrew",
            LATIN_DATE_REGEX,
            0.6
        ), 
        Pattern(
          "dates written in English",
          EN_DATE_REGEX,
          0.6
        ),               
    ]

    SUPPORTED_ENTITY = "LATIN_DATE"
    
    def __init__(self):
        """
        Initializes the IdRecognizer object
        """
        super().__init__(supported_entity=HebLatinDateRecognizer.SUPPORTED_ENTITY,
                         patterns=HebLatinDateRecognizer.PATTERNS, name="HebLatinDateRecognizer",                         
                         supported_language="he"
                         )

    