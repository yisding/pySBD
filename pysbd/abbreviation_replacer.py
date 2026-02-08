# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import List

from pysbd.utils import apply_rules


def replace_pre_number_abbr(txt: str, abbr: str) -> str:
    # prepend a space to avoid needing another regex for start of string
    txt = " " + txt
    escaped = re.escape(abbr.strip())
    txt = re.sub(rf"(?<=\s{escaped})\.(?=(\s\d|\s+\())", "∯", txt)
    # remove the prepended space
    txt = txt[1:]
    return txt


def replace_prepositive_abbr(txt: str, abbr: str) -> str:
    # prepend a space to avoid needing another regex for start of string
    txt = " " + txt
    escaped = re.escape(abbr.strip())
    txt = re.sub(rf"(?<=\s{escaped})\.(?=(\s|:\d+))", "∯", txt)
    # remove the prepended space
    txt = txt[1:]
    return txt


class AbbreviationReplacer:
    def __init__(self, text: str, lang) -> None:
        self.text = text
        self.lang = lang
        self._abbreviations = sorted(
            self.lang.Abbreviation.ABBREVIATIONS,
            key=len,
            reverse=True,
        )

    def replace(self) -> str:
        self.text = apply_rules(
            self.text,
            self.lang.PossessiveAbbreviationRule,
            self.lang.KommanditgesellschaftRule,
            *self.lang.SingleLetterAbbreviationRules.All
        )
        lines: List[str] = []
        for line in self.text.splitlines(True):
            lines.append(self.search_for_abbreviations_in_string(line))
        self.text = "".join(lines)
        self.replace_multi_period_abbreviations()
        self.text = apply_rules(self.text, *self.lang.AmPmRules.All)
        self.text = self.replace_abbreviation_as_sentence_boundary()
        return self.text

    def replace_abbreviation_as_sentence_boundary(self) -> str:
        sent_starters = "|".join((r"(?=\s{}\s)".format(word) for word in self.SENTENCE_STARTERS))
        regex = r"(U∯S|U\.S|U∯K|E∯U|E\.U|U∯S∯A|U\.S\.A|I|i.v|I.V)∯({})".format(sent_starters)
        self.text = re.sub(regex, '\\1.', self.text)
        return self.text

    def replace_multi_period_abbreviations(self) -> None:
        def mpa_replace(match):
            match = match.group()
            match = re.sub(re.escape(r"."), "∯", match)
            return match

        self.text = re.sub(
            self.lang.MULTI_PERIOD_ABBREVIATION_REGEX,
            mpa_replace,
            self.text,
            flags=re.IGNORECASE
        )

    def replace_period_of_abbr(self, txt: str, abbr: str) -> str:
        # prepend a space to avoid needing another regex for start of string
        txt = " " + txt
        txt = re.sub(
            r"(?<=\s{abbr})\.(?=((\.|\:|-|\?|,)|(\s([a-z]|I\s|I'm|I'll|\d|\())))".format(
                abbr=re.escape(abbr.strip())
            ),
            "∯",
            txt,
        )
        # remove the prepended space
        txt = txt[1:]
        return txt


    def search_for_abbreviations_in_string(self, text: str) -> str:
        lowered = text.lower()
        for abbr in self._abbreviations:
            stripped = abbr.strip()
            stripped_lower = stripped.lower()
            if stripped_lower not in lowered:
                continue
            escaped = re.escape(stripped)
            abbrev_match = re.findall(
                r"(?:^|\s|\r|\n){}".format(escaped), text, flags=re.IGNORECASE
            )
            if not abbrev_match:
                continue
            next_word_start = r"(?<={" + str(re.escape(stripped)) + "} ).{1}"
            char_array = re.findall(next_word_start, text)
            for ind, match in enumerate(abbrev_match):
                text = self.scan_for_replacements(
                    text, match, ind, char_array
                )
        return text

    def scan_for_replacements(self, txt: str, am: str, ind: int, char_array) -> str:
        try:
            char = char_array[ind]
        except IndexError:
            char = ""
        prepositive = self.lang.Abbreviation.PREPOSITIVE_ABBREVIATIONS
        number_abbr = self.lang.Abbreviation.NUMBER_ABBREVIATIONS
        upper = str(char).isupper()
        if not upper or am.strip().lower() in prepositive:
            if am.strip().lower() in prepositive:
                txt = replace_prepositive_abbr(txt, am)
            elif am.strip().lower() in number_abbr:
                txt = replace_pre_number_abbr(txt, am)
            else:
                txt = self.replace_period_of_abbr(txt, am)
        return txt
