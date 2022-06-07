from typing import Optional, List
from presidio_analyzer.predefined_recognizers import DateRecognizer
from presidio_analyzer import Pattern
from hebsafeharbor.common.date_regex import SPLIT_BY_SPACE_REGEX


class NoisyDateRecognizer(DateRecognizer):
    """
    A class which extends the DateRecognizer (@Presidio) and recognizes dates that are not separated from the surrounded
    text or includes spaces around the delimiters
    """   
    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "he",
        supported_entity: str = "NOISY_DATE",
    ):
        # take the default patterns from the DateRecognizer class and remove the b
        patterns = self.PATTERNS
        AUG_PATTERNS = []
        for p in patterns:
            pattern_dict = p.to_dict()
            pattern = pattern_dict['regex']
            pattern_with_no_b = pattern.replace(r"\b", "")
            pattern_dict['regex'] = pattern_with_no_b
            AUG_PATTERNS.append(Pattern.from_dict(pattern_dict))

        # dates that may have spaces around the delimiters
        PATTERNS = [Pattern(
            r"yyyy ?\s[.\-]?\s mm ?\s[.\-]?\s dd",
            SPLIT_BY_SPACE_REGEX,
            0.6)]
        AUG_PATTERNS = AUG_PATTERNS + PATTERNS
        super().__init__(
            supported_entity=supported_entity,
            patterns=AUG_PATTERNS,
            context=context,
            supported_language=supported_language,
        )

