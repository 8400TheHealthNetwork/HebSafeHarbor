from typing import Optional, Dict

from presidio_analyzer.nlp_engine import SpacyNlpEngine, NlpArtifacts
from spacy.tokens import Doc


class HebSpacyNlpEngine(SpacyNlpEngine):
    """
    Wrapper class for SpacyNlpEngine, for cases where lemmas are not provided by the spaCy pipeline.
    Replaces lemmas with the original token text.
    """

    def __init__(self, models: Optional[Dict[str, str]] = None):
        if not models:
            models = {"he": "he_ner_news_trf"}
        super().__init__(models=models)

    def _doc_to_nlp_artifact(self, doc: Doc, language: str) -> NlpArtifacts:
        tokens_indices = [token.idx for token in doc]
        entities = doc.ents
        return NlpArtifacts(
            entities=entities,
            tokens=doc,
            tokens_indices=tokens_indices,
            lemmas=[token.text for token in doc],
            nlp_engine=self,
            language=language,
        )
