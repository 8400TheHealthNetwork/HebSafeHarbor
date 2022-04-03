from typing import Optional

from presidio_analyzer import PatternRecognizer, Pattern
from hebsafeharbor.common.date_regex import HEB_FULL_DATE_REGEX,HEB_MONTH_YEAR_REGEX,HEB_DAY_MONTH_REGEX

class HebDateRecognizer(PatternRecognizer):
    """
    A class which extends the PatternRecognizer (@Presidio) and responsible for the recognition of Hebrew dates (א׳ בתשרי תש״ח)
    """
    PATTERNS = [
        Pattern(
            "Hebrew full date",  
            HEB_FULL_DATE_REGEX,
            0.6
        ),  
        Pattern(
            "Hebrew month year",  
            HEB_MONTH_YEAR_REGEX,
            0.6
        ),      
        Pattern(
            "Hebrew day month",  
            HEB_DAY_MONTH_REGEX,
            0.6
        ),        
        
    ]

    SUPPORTED_ENTITY = "HEBREW_DATE"
    
    def __init__(self):
        """
        Initializes the IdRecognizer object
        """
        super().__init__(supported_entity=HebDateRecognizer.SUPPORTED_ENTITY,
                         patterns=HebDateRecognizer.PATTERNS, name="HebDateRecognizer",                         
                         supported_language="he"
                         )

    