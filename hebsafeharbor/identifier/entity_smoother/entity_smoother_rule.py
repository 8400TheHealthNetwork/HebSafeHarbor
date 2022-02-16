from abc import ABCMeta, abstractmethod
from typing import List, Callable

from presidio_analyzer import RecognizerResult

from hebsafeharbor import Doc


class EntitySmootherRule(metaclass=ABCMeta):
    """
    An abstract class which represents a rule which smooths some entities according to some policy. If the requirement
    it holds is satisfied, it performs some smoothing action.
    """

    def __init__(self, name: str, requirement: Callable[[List[RecognizerResult], Doc], bool]):
        """
        Initializing EntitySmootherRule by defining its name and the requirement it verifies
        :param name: the name of the rule
        :param requirement: the condition that must be satisfied for executing the rule
        """
        self.name = name
        self.requirement = requirement

    @abstractmethod
    def __call__(self, doc: Doc) -> Doc:
        """
        Executes the EntityExpanderRule on a list of entities by checking if the requirement is
        satisfied and return the updated Doc object after performing some action

        :param doc: doc object
        :return an updated Doc object after executing the rule
        """
        pass
