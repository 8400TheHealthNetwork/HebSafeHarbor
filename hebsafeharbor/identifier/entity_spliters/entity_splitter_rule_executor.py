import copy

from hebsafeharbor import Doc
from hebsafeharbor.identifier.entity_spliters.date_entity_splitter import DateEntitySplitter

class EntitySplitterRuleExecutor:
    """
    Triggers the different entity splitters over the consolidated recognized entities (exist in the input Doc object).
    Note that after calling the executor the entities can possibly changed
    """

    def __init__(self):
        """
        Initializing the EntitySplitterRuleExecutor
        """

        # rules
        self.date_entity_splitter = DateEntitySplitter()

    def __call__(self, doc: Doc) -> Doc:
        """
        Execute the different entity smoothing rules one by one where each rule performed on the output set of
        entities of the previous one and according to some conditions.

        :param doc: document object
        :return an updated document after triggering the entity splitters
        """

        # initialize the entity splitter section in Doc with a deep copy of the consolidated recognized entities
        doc.granular_analyzer_results = copy.deepcopy(doc.consolidated_results)

        # trigger the first entity splitter which decides for each DATE entity whether it is BIRTH_DATE or MEDICAL_DATE
        doc = self.date_entity_splitter(doc)

        return doc
