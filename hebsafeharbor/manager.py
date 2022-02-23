from typing import Dict, List

from hebsafeharbor import Doc
from hebsafeharbor.anonymizer.phi_anonymizer import PhiAnonymizer
from hebsafeharbor.identifier.phi_identifier import PhiIdentifier

class HebSafeHarbor:
    """
    The manager of the application. When it called, given a Hebrew text, it executes the identification and
    anonymization process and return an anonymized text.
    """

    def __init__(self):
        """
        Initializes HebSafeHarbor
        """
        self.identifier = PhiIdentifier()
        self.anonymizer = PhiAnonymizer()

    def __call__(self, doc_list: List[Dict[str, str]]) -> List[Doc]:
        """
        The main method, executes the PHI reduction process on the given text
        :param doc_list: List of dictionary where each dict represents a document.
                        Each dictionary should consist of "id" and "text" columns
        :return: anonymized text
        """
        docs = [Doc(doc_dict) for doc_dict in doc_list]
        docs = self.identify(docs)
        docs = self.anonymize(docs)
        return docs

    def identify(self, docs: List[Doc]) -> List[Doc]:
        """
        This method identifies the PHI entities in the input text
        :param docs: a list of Doc objects which contains the input text for anonymization
        :return: a list of the updated Doc objects that contains the recognized PHI entities
        """
        return [self.identifier(doc) for doc in docs]

    def anonymize(self, docs: List[Doc]) -> List[Doc]:
        """
        This method anonymizes the recognized PHI entities using different techniques
        :param doc: a list of Doc objects which contains the consolidated recognized PHI entities
        :return: a list of the updated Doc objects that contains the anonymized text
        """
        return [self.anonymizer(doc) for doc in docs]

    @staticmethod
    def create_result(doc: Doc) -> Dict[str, str]:
        """
        this function will get a document and create a result map.
        """

        items = []
        for item in doc.anonymized_text.items:
            item_result = {
                "startPosition": item.start,
                "endPosition": item.end,
                "entityType": item.entity_type,
                "text": doc.text[item.start:item.end],
                "mask": item.text,
                "operator": item.operator
            }
            items.append(item_result)

        result: Dict = {
            "id": doc.id,
            "text": doc.anonymized_text.text,
            "items": items
        }
        return result
