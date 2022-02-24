import re
from typing import List, Tuple, Optional
import ahocorasick


class TermsRecognizer:

    def __init__(self, phrase_list: List[str]):
        """
        Initializes TermsRecognizer
        :param phrase_list: list of terms to recognize
        """
        self._automaton = ahocorasick.Automaton(ahocorasick.STORE_LENGTH)
        for phrase in phrase_list:
            self._automaton.add_word(phrase)
        self._automaton.make_automaton()

    def __call__(self, text: str, prefixes: Optional[List[str]] = None) -> List[Tuple[int, int]]:
        """
        This method searches for terms in text
        :param text: text
        :return: List of starting offsets of matches and their length
        """
        offsets = []
        for end_index_short, length in self._automaton.iter(text):
            offset = end_index_short - length + 1
            if length == 1 or offset < 0 or offset >= len(text):
                pass
            else:
                if prefixes:
                    prefixes_pattern_raw = "|".join(prefixes)
                    prefixes_pattern = r"\W(" + prefixes_pattern_raw + ")"
                    start_cond = offset == 0 or re.match(r"\W", text[offset - 1]) or re.match(prefixes_pattern, text[
                                                                                                                offset - 2:offset]) or (
                                             offset == 1 and re.match(prefixes_pattern_raw, text[offset - 1]))
                else:
                    start_cond = offset == 0 or re.match(r"\W", text[offset - 1])
                is_phrase = start_cond \
                            and (offset + length == len(text)
                                 or re.match(r"\W", text[offset + length]))
                if is_phrase:
                    offsets.append((offset, length))

        # drop duplicates
        offsets = list(set(offsets))

        return offsets
