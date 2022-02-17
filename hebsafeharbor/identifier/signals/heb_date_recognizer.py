from typing import Optional

from presidio_analyzer import PatternRecognizer, Pattern
from hebsafeharbor.common.date_regex import HEB_DATE_REGEX

class HebDateRecognizer(PatternRecognizer):
    """
    A class which extends the PatternRecognizer (@Presidio) and responsible for the recognition of Hebrew dates (א׳ בתשרי תש״ח)
    """
    PATTERNS = [
        Pattern(
            "Hebrew full date",  
            HEB_DATE_REGEX,
            0.6
        ),        
        
    ]

    SUPPORTED_ENTITY = "DATE"
    
    def __init__(self):
        """
        Initializes the IdRecognizer object
        """
        super().__init__(supported_entity=HebDateRecognizer.SUPPORTED_ENTITY,
                         patterns=HebDateRecognizer.PATTERNS, name="HebDateRecognizer",                         
                         supported_language="he"
                         )

    