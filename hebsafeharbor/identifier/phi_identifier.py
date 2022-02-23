from typing import List

from hebsafeharbor.common.city_utils import BELOW_THRESHOLD_CITIES_LIST, ABOVE_THRESHOLD_CITIES_LIST, \
    ABBREVIATIONS_LIST, AMBIGOUS_BELOW_THRESHOLD_CITIES_LIST, AMBIGOUS_ABOVE_THRESHOLD_CITIES_LIST, \
    AMBIGUOUS_CITIES_CONTEXT
from hebsafeharbor.common.country_utils import COUNTRY_DICT
from hebsafeharbor.common.document import Doc
from hebsafeharbor.common.prepositions import LOCATION_PREPOSITIONS, DISEASE_PREPOSITIONS, MEDICATION_PREPOSITIONS, \
    MEDICAL_TEST_PREPOSITIONS
from hebsafeharbor.identifier import HebSpacyNlpEngine
from hebsafeharbor.identifier.consolidation.consolidator import NerConsolidator
from hebsafeharbor.identifier.entity_smoother.entity_smoother_rule_executor import EntitySmootherRuleExecutor
from hebsafeharbor.identifier.entity_spliters.entity_splitter_rule_executor import EntitySplitterRuleExecutor
from hebsafeharbor.identifier.signals.general_id_recognizer import GeneralIdRecognizer

from hebsafeharbor.identifier.signals.heb_date_recognizer import HebDateRecognizer
from hebsafeharbor.identifier.signals.heb_preposition_date_recognizer import PrepositionDateRecognizer
from hebsafeharbor.identifier.signals.heb_latin_date_recognizer import HebLatinDateRecognizer
from hebsafeharbor.identifier.signals.hebrew_city_recognizer import AmbiguousHebrewCityRecognizer
from hebsafeharbor.identifier.signals.israeli_id_recognizer import IsraeliIdNumberRecognizer
from presidio_analyzer import AnalyzerEngine, LocalRecognizer, RecognizerRegistry
from presidio_analyzer.predefined_recognizers import CreditCardRecognizer, DateRecognizer, EmailRecognizer, \
    IpRecognizer, PhoneRecognizer, SpacyRecognizer, UrlRecognizer

from hebsafeharbor.identifier.signals.lexicon_based_recognizer import LexiconBasedRecognizer
from hebsafeharbor.lexicons.disease import DISEASES
from hebsafeharbor.lexicons.medical_device import MEDICAL_DEVICE
from hebsafeharbor.lexicons.medical_tests import MEDICAL_TESTS
from hebsafeharbor.lexicons.medications import MEDICATIONS


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
        ner_signals.append(UrlRecognizer(supported_language="he", context=["אתר אינטרנט"]))

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
        ner_signals.append(LexiconBasedRecognizer("CountryRecognizer", "COUNTRY", COUNTRY_DICT.keys(),
                                                  allowed_prepositions=LOCATION_PREPOSITIONS))
        # init Hebrew city recognizers
        cities_set = set(BELOW_THRESHOLD_CITIES_LIST).union(
            set(ABOVE_THRESHOLD_CITIES_LIST)).union(set(ABBREVIATIONS_LIST))
        ambiguous_cities_set = set(
            AMBIGOUS_BELOW_THRESHOLD_CITIES_LIST).union(
            set(AMBIGOUS_ABOVE_THRESHOLD_CITIES_LIST))
        disambiguated_cities_set = cities_set - ambiguous_cities_set
        ner_signals.append(LexiconBasedRecognizer("IsraeliCityRecognizer", "CITY",
                                                  disambiguated_cities_set,
                                                  allowed_prepositions=LOCATION_PREPOSITIONS))
        # ner_signals.append(AmbiguousHebrewCityRecognizer("AmbiguousIsraeliCityRecognizer", "CITY",
        #                                                  ambiguous_cities_set,
        #                                                  allowed_prepositions=LOCATION_PREPOSITIONS,
        #                                                  endorsing_entities=['LOC', 'GPE'],
        #                                                  context=AMBIGUOUS_CITIES_CONTEXT,
        #                                                  ),
        #                    )
        
        # init disease recognizer
        ner_signals.append(
            LexiconBasedRecognizer("DiseaseRecognizer", "DISEASE", DISEASES, allowed_prepositions=DISEASE_PREPOSITIONS))
        # init medication recognizer
        ner_signals.append(
            LexiconBasedRecognizer("MedicationRecognizer", "MEDICATION", MEDICATIONS,
                                   allowed_prepositions=MEDICATION_PREPOSITIONS))
        # init medical tests recognizer
        ner_signals.append(
            LexiconBasedRecognizer("MedicalTestRecognizer", "MEDICAL_TEST", MEDICAL_TESTS + MEDICAL_DEVICE,
                                   allowed_prepositions=MEDICAL_TEST_PREPOSITIONS))
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
