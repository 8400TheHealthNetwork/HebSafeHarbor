import copy

from hebsafeharbor import Doc
from hebsafeharbor.identifier.entity_smoother.location_merger_rule import LocationsMergerRule


class EntitySmootherRuleExecutor:
    """
    Applies the entity smoothing rules over the recognized entities (stored in the input Doc object).
    Note that after calling the executor the results are saved in smoothed_entities section in the Doc.
    """

    def __init__(self):
        """
        Initializing the EntitySmootherRuleExecutor
        """

        # rules
        self.locations_merger_rule = LocationsMergerRule()

    def __call__(self, doc: Doc) -> Doc:
        """
        Execute the different entity smoothing rules one by one where each rule performed on the output set of
        entities of the previous one and according to some conditions.

        :param doc: document object
        :return an updated document after performing the rules
        """

        # initialize the entity smoother section in Doc with a deep copy of the recognized entities
        doc.smoothed_entities = copy.deepcopy(doc.analyzer_results)

        # apply first rule - merge two consecutive LOC entities if there is a number between them
        doc = self.locations_merger_rule(doc)
        return doc
