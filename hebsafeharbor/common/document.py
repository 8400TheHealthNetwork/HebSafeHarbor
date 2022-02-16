import uuid
from typing import List, Dict

from presidio_analyzer import RecognizerResult
from presidio_anonymizer.entities import EngineResult


class Doc:
    """
    This class serves as a container for the information gained as part of the entire PHI reduction process
    (identification and anonymization)
    """

    def __init__(self, data: Dict[str, str]):
        """
        Doc initialization
        :param text: the input text for the PHI reduction process
        """
        self.metadata = data
        self.text = None
        self.id = None
        if "text" in self.metadata:
            self.text = data["text"]
        else:
            message = "Could not find \'text\' in data"
            raise ValueError(message)
        if "id" in self.metadata:
            self.id = str(data["id"])
        else:
            # create a synthetic id
            self.id = str(uuid.uuid4())
        self.analyzer_results: List[RecognizerResult] = []
        self.smoothed_entities: List[RecognizerResult] = []
        self.consolidated_results: List[RecognizerResult] = []
        self.granular_analyzer_results: List[RecognizerResult] = []
        self.anonymized_text: EngineResult = []
