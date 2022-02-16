from typing import List

from hebsafeharbor.common.document import Doc
from hebsafeharbor.identifier import HebSpacyNlpEngine
from hebsafeharbor.identifier.consolidation.consolidator import NerConsolidator
from hebsafeharbor.identifier.entity_smoother.entity_smoother_rule_executor import EntitySmootherRuleExecutor
from hebsafeharbor.identifier.entity_spliters.entity_splitter_rule_executor import EntitySplitterRuleExecutor
from hebsafeharbor.identifier.signals.country_recognizer import CountryRecognizer
from hebsafeharbor.identifier.signals.general_id_recognizer import GeneralIdRecognizer

from hebsafeharbor.identifier.signals.heb_date_recognizer import HebDateRecognizer
from hebsafeharbor.identifier.signals.heb_preposition_date_recognizer import PrepositionDateRecognizer
from hebsafeharbor.identifier.signals.heb_latin_date_recognizer import HebLatinDateRecognizer
from hebsafeharbor.identifier.signals.israeli_city_recognizer import IsraeliCityRecognizer
from hebsafeharbor.identifier.signals.israeli_id_recognizer import IsraeliIdNumberRecognizer
from presidio_analyzer import AnalyzerEngine, LocalRecognizer, RecognizerRegistry
from presidio_analyzer.predefined_recognizers import CreditCardRecognizer, DateRecognizer, EmailRecognizer, \
    IpRecognizer, PhoneRecognizer, SpacyRecognizer


class PhiIdentifier:
    """
    This class is responsible on the identification process, recognize entities using the AnalyzerEngine (@Presidio) and
    consolidate them using NERConsolidator.
    """

    def __init__(self):
        """
        Initializes the PhiIdentifier which is composed of Presidio analyzer and NerConsolidator
        """

        self.analyzer = self._init_presidio_analyzer()
        self.entity_smoother = EntitySmootherRuleExecutor()
        self.entity_splitter = EntitySplitterRuleExecutor()
        self.consolidator = NerConsolidator()

    def __call__(self, doc: Doc) -> Doc:
        """
        This method identifies the PHI entities

        :param doc: Doc object which holds the input text for PHI reduction
        :return: an updated Doc object that contains the the set of entities that were recognized by the different
        signals and the consolidated set of entities
        """

        # recognition
        analyzer_results = self.analyzer.analyze(text=doc.text, language="he", return_decision_process=True)
        doc.analyzer_results = sorted(analyzer_results, key=lambda res: res.start)

        # entity smoothing
        doc = self.entity_smoother(doc)

        # consolidation
        doc = self.consolidator(doc)

        # entity splitter
        doc = self.entity_splitter(doc)

        return doc

    def _init_presidio_analyzer(self) -> AnalyzerEngine:
        """
        Creates and initializes the Presidio analyzer
        :return: Presidio analyzer
        """

        # create NLP engine based on the nlp configuration
        nlp_engine = HebSpacyNlpEngine(models={"he": "he_ner_news_trf"})

        # initialize the signals
        signals = self._init_analyzer_signals()
        # create the signals registry
        registry = RecognizerRegistry()
        # add the different signals to registry
        for signal in signals:
            registry.add_recognizer(signal)

        # create the AnalyzerEngine using the created registry, NLP engine and supported_languages
        analyzer = AnalyzerEngine(
            registry=registry,
            nlp_engine=nlp_engine,
            supported_languages=["he"]
        )

        return analyzer

    def _init_analyzer_signals(self) -> List[LocalRecognizer]:
        """
        Creates and initializes the analyzer's NER signals

        :return: a list of NER initialized signals
        """

        ner_signals = []

        # presidio predefined recognizers
        ner_signals.append(CreditCardRecognizer(supported_language="he", context=["כרטיס", "אשראי"]))
        ner_signals.append(
            DateRecognizer(supported_language="he", context=["תאריך", "לידה", "הולדת", "נולד", "נולדה", "נולדו"]))
        ner_signals.append(
            EmailRecognizer(supported_language="he", context=["אימייל", "דואל", "email", "דואר אלקטרוני"]))
        ner_signals.append(IpRecognizer(supported_language="he", context=["IP", "כתובת IP", "כתובת איי פי"]))
        ner_signals.append(PhoneRecognizer(supported_language="he", context=["טלפון", "סלולרי", "פקס"]))

        hebspacy_recognizer = self.init_hebspacy_recognizer()

        ner_signals.append(hebspacy_recognizer)
        # init Israeli id number recognizer
        ner_signals.append(IsraeliIdNumberRecognizer())
        # init general id recognizer
        ner_signals.append(GeneralIdRecognizer())
        # init dates in hebrew
        ner_signals.append(HebDateRecognizer())
        # init dates with preposition
        ner_signals.append(PrepositionDateRecognizer())
        # init latin dates
        ner_signals.append(HebLatinDateRecognizer())
        # init Hebrew country recognizer
        ner_signals.append(CountryRecognizer(supported_language="he"))
        # init Hebrew city recognizer
        ner_signals.append(IsraeliCityRecognizer(supported_language="he"))

        return ner_signals

    def init_hebspacy_recognizer(self):
        """
        Adapt the SpacyRecognizer to fit the specific entities of HebSpacy.
        """

        hebspacy_entities = ["PERS", "LOC", "ORG", "TIME", "DATE", "MONEY", "PERCENT", "MISC__AFF", "MISC__ENT",
                             "MISC_EVENT", "PER", "GPE", "FAC", "WOA", "EVE", "DUC", "ANG"]
        hebspacy_label_groups = [
            ({ent}, {ent}) for ent in hebspacy_entities
        ]
        hebspacy_recognizer = SpacyRecognizer(supported_language="he",
                                              supported_entities=hebspacy_entities,
                                              ner_strength=1.0,
                                              check_label_groups=hebspacy_label_groups)
        return hebspacy_recognizer
