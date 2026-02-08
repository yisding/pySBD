# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import List

from pysbd.utils import apply_rules
from pysbd.lists_item_replacer import ListItemReplacer
from pysbd.exclamation_words import ExclamationWords
from pysbd.between_punctuation import BetweenPunctuation
from pysbd.abbreviation_replacer import AbbreviationReplacer

class Processor:

    def __init__(self, text: str | None, lang, char_span: bool = False) -> None:
        """Process a text - do pre and post processing - to get proper sentences

        Parameters
        ----------
        text : str
            Original text
        language : object
            Language module
        char_span : bool, optional
            Get start & end character offsets of each sentences
            within original text, by default False
        """
        self.text = text
        self.lang = lang
        self.char_span = char_span

    def process(self) -> List[str]:
        if not self.text:
            return []
        self.text = self.text.replace('\n', '\r')
        li = ListItemReplacer(self.text)
        self.text = li.add_line_break()
        self.replace_abbreviations()
        self.replace_numbers()
        self.replace_continuous_punctuation()
        self.replace_periods_before_numeric_references()
        self.text = apply_rules(
            self.text,
            self.lang.Abbreviation.WithMultiplePeriodsAndEmailRule,
            self.lang.GeoLocationRule, self.lang.FileFormatRule)
        postprocessed_sents = self.split_into_segments()
        return postprocessed_sents

    def rm_none_flatten(self, sents: List[str | List[str] | None]) -> List[str]:
        """Remove None values and unpack list of list sents

        Parameters
        ----------
        sents : list
            list of sentences

        Returns
        -------
        list
            unpacked and None removed list of sents
        """
        sents = [s for s in sents if s]
        if not any(isinstance(s, list) for s in sents):
            return sents
        new_sents = []
        for sent in sents:
            if isinstance(sent, list):
                for s in sent:
                    new_sents.append(s)
            else:
                new_sents.append(sent)
        return new_sents

    def split_into_segments(self) -> List[str]:
        self.check_for_parens_between_quotes()
        sents = self.text.split('\r')
        # remove empty and none values
        sents = self.rm_none_flatten(sents)
        sents = [
            apply_rules(s, self.lang.SingleNewLineRule, *self.lang.EllipsisRules.All)
            for s in sents
        ]
        sents = [self.check_for_punctuation(s) for s in sents]
        # flatten list of list of sentences
        sents = self.rm_none_flatten(sents)
        postprocessed_sents = []
        for sent in sents:
            sent = apply_rules(sent, *self.lang.SubSymbolsRules.All)
            for pps in self.post_process_segments(sent):
                if pps:
                    postprocessed_sents.append(pps)
        postprocessed_sents = [apply_rules(ns, self.lang.SubSingleQuoteRule)
                               for ns in postprocessed_sents]
        return postprocessed_sents

    def post_process_segments(self, txt: str) -> List[str]:
        if len(txt) > 2 and re.search(r'\A[a-zA-Z]*\Z', txt):
            return [txt]

        txt = apply_rules(txt, *self.lang.ReinsertEllipsisRules.All)
        if re.search(self.lang.QUOTATION_AT_END_OF_SENTENCE_REGEX, txt):
            txt = re.split(
                self.lang.SPLIT_SPACE_QUOTATION_AT_END_OF_SENTENCE_REGEX, txt)
            return [t for t in txt if t]
        else:
            txt = txt.replace('\n', '')
            txt = txt.strip()
            return [txt] if txt else []

    def check_for_parens_between_quotes(self) -> None:
        def paren_replace(match):
            match = match.group()
            sub1 = re.sub(r'\s(?=\()', '\r', match)
            sub2 = re.sub(r'(?<=\))\s', '\r', sub1)
            return sub2
        self.text = re.sub(self.lang.PARENS_BETWEEN_DOUBLE_QUOTES_REGEX,
                      paren_replace, self.text)

    def replace_continuous_punctuation(self) -> None:
        def continuous_puncs_replace(match):
            match = match.group()
            sub1 = re.sub(re.escape('!'), '&ᓴ&', match)
            sub2 = re.sub(re.escape('?'), '&ᓷ&', sub1)
            return sub2
        self.text = re.sub(self.lang.CONTINUOUS_PUNCTUATION_REGEX,
                        continuous_puncs_replace, self.text)

    def replace_periods_before_numeric_references(self) -> None:
         # https://github.com/diasks2/pragmatic_segmenter/commit/d9ec1a352aff92b91e2e572c30bb9561eb42c703
        self.text = re.sub(self.lang.NUMBERED_REFERENCE_REGEX,
                      r"∯\2\r\7", self.text)

    def consecutive_underscore(self, txt: str) -> bool:
        # Rubular: http://rubular.com/r/fTF2Ff3WBL
        txt = re.sub(r'_{3,}', '', txt)
        return len(txt) == 0

    def check_for_punctuation(self, txt: str) -> List[str]:
        if any(p in txt for p in self.lang.Punctuations):
            sents = self.process_text(txt)
            return sents
        else:
            # NOTE: next steps of check_for_punctuation will unpack this list
            return [txt]

    def process_text(self, txt: str) -> List[str]:
        if txt[-1] not in self.lang.Punctuations:
            txt += 'ȸ'
        txt = ExclamationWords.apply_rules(txt)
        txt = self.between_punctuation(txt)
        # handle text having only doublepunctuations
        if not re.match(self.lang.DoublePunctuationRules.DoublePunctuation, txt):
            txt = apply_rules(txt, *self.lang.DoublePunctuationRules.All)
        txt = apply_rules(txt, self.lang.QuestionMarkInQuotationRule,
                              *self.lang.ExclamationPointRules.All)
        txt = ListItemReplacer(txt).replace_parens()
        txt = self.sentence_boundary_punctuation(txt)
        return txt

    def replace_numbers(self) -> None:
        self.text = apply_rules(self.text, *self.lang.Numbers.All)

    def abbreviations_replacer(self):
        if hasattr(self.lang, "AbbreviationReplacer"):
            return self.lang.AbbreviationReplacer(self.text, self.lang)
        else:
            return AbbreviationReplacer(self.text, self.lang)

    def replace_abbreviations(self) -> None:
        self.text = self.abbreviations_replacer().replace()

    def between_punctuation_processor(self, txt: str):
        if hasattr(self.lang, "BetweenPunctuation"):
            return self.lang.BetweenPunctuation(txt)
        else:
            return BetweenPunctuation(txt)

    def between_punctuation(self, txt: str) -> str:
        txt = self.between_punctuation_processor(txt).replace()
        return txt

    def sentence_boundary_punctuation(self, txt: str) -> List[str]:
        if hasattr(self.lang, 'ReplaceColonBetweenNumbersRule'):
            txt = apply_rules(txt, self.lang.ReplaceColonBetweenNumbersRule)
        if hasattr(self.lang, 'ReplaceNonSentenceBoundaryCommaRule'):
            txt = apply_rules(txt, self.lang.ReplaceNonSentenceBoundaryCommaRule)
        # retain exclamation mark if it is an ending character of a given text
        txt = re.sub(r'&ᓴ&$', '!', txt)
        txt = [
            m.group() for m in re.finditer(self.lang.SENTENCE_BOUNDARY_REGEX, txt)
            ]
        return txt
