# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pysbd.utils import Rule, apply_rules


class EscapeRegexReservedCharacters:
    LeftParen = Rule(r'\(', '\\(')
    RightParen = Rule(r'\)', '\\)')
    LeftBracket = Rule(r'\[', '\\[')
    RightBracket = Rule(r'\]', '\\]')
    Dash = Rule(r'\-', '\\-')

    All = [LeftParen, RightParen, LeftBracket, RightBracket, Dash]


class SubEscapedRegexReservedCharacters:
    SubLeftParen = Rule(r'\\\(', '(')
    SubRightParen = Rule(r'\\\)', ')')
    SubLeftBracket = Rule(r'\\\[', '[')
    SubRightBracket = Rule(r'\\\]', ']')
    SubDash = Rule(r'\\\-', '-')

    All = [
        SubLeftParen, SubRightParen, SubLeftBracket, SubRightBracket, SubDash
    ]


_DOT_RE = re.compile(r'\.')
_FULLWIDTH_PERIOD_RE = re.compile(r'\。')
_SPECIAL_PERIOD_RE = re.compile(r'\．')
_FULLWIDTH_EXCLAMATION_RE = re.compile(r'\！')
_EXCLAMATION_RE = re.compile(r'!')
_QUESTION_RE = re.compile(r'\?')
_FULLWIDTH_QUESTION_RE = re.compile(r'\？')
_APOSTROPHE_RE = re.compile(r"'")


def replace_punctuation(match, match_type: str | None = None) -> str:
    text = apply_rules(match.group(), *EscapeRegexReservedCharacters.All)
    sub = _DOT_RE.sub('∯', text)
    sub_1 = _FULLWIDTH_PERIOD_RE.sub('&ᓰ&', sub)
    sub_2 = _SPECIAL_PERIOD_RE.sub('&ᓱ&', sub_1)
    sub_3 = _FULLWIDTH_EXCLAMATION_RE.sub('&ᓳ&', sub_2)
    sub_4 = _EXCLAMATION_RE.sub('&ᓴ&', sub_3)
    sub_5 = _QUESTION_RE.sub('&ᓷ&', sub_4)
    last_sub = _FULLWIDTH_QUESTION_RE.sub('&ᓸ&', sub_5)
    if match_type != 'single':
        last_sub = _APOSTROPHE_RE.sub('&⎋&', last_sub)
    text = apply_rules(last_sub, *SubEscapedRegexReservedCharacters.All)
    return text
