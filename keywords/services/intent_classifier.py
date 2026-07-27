"""
Intent Classification Service
Rule-based classifier that assigns one of four search intents to a keyword.

Intent taxonomy:
  Informational  – user wants to learn something        ("how to", "what is", "guide")
  Transactional  – user wants to buy / complete an act  ("buy", "order", "download")
  Commercial     – user is researching before buying     ("best", "review", "vs")
  Navigational   – user wants to reach a specific site   ("login", "website", "official")
"""

import re
from typing import Dict

# Pattern sets are ordered from most specific → least specific so that
# a keyword matching multiple groups lands in the most precise bucket.
INTENT_PATTERNS: Dict[str, list[re.Pattern]] = {
    "navigational": [
        re.compile(r"\b(login|sign in|sign up|register|account|official|website|site|app|portal|dashboard|download|install)\b", re.I),
        re.compile(r"\b(homepage|home page|contact|support page)\b", re.I),
    ],
    "transactional": [
        re.compile(r"\b(buy|purchase|order|shop|checkout|add to cart|subscribe|hire|book|reserve|get)\b", re.I),
        re.compile(r"\b(for sale|on sale|discount|coupon|promo|deal|offer|cheap|affordable|price|cost|fee|quote)\b", re.I),
        re.compile(r"\b(near me|delivery|shipping|free trial)\b", re.I),
    ],
    "commercial": [
        re.compile(r"\b(best|top|review|reviews|rating|ratings|comparison|compare|vs\.?|versus|alternative|alternatives|recommendation|recommended|worth it)\b", re.I),
        re.compile(r"\b(pros and cons|advantages|disadvantages|difference between)\b", re.I),
        re.compile(r"\b(\d+\s+(best|top|picks|options|choices))\b", re.I),
    ],
    "informational": [
        re.compile(r"\b(how to|how do|how can|how does|how is|how are|how much|how many)\b", re.I),
        re.compile(r"\b(what is|what are|what does|what can|what should)\b", re.I),
        re.compile(r"\b(why is|why are|why does|why do|why should)\b", re.I),
        re.compile(r"\b(when is|when are|when does|when to)\b", re.I),
        re.compile(r"\b(who is|who are|who can|who should)\b", re.I),
        re.compile(r"\b(where is|where are|where to|where can)\b", re.I),
        re.compile(r"\b(guide|tutorial|tips|tricks|examples|explained|definition|meaning|overview|introduction|basics|beginner|learn|understand|course|lesson)\b", re.I),
    ],
}

# Default when no pattern matches
DEFAULT_INTENT = "informational"


class IntentClassifierService:
    """
    Classifies the search intent of a keyword string.

    The classifier applies ordered regex pattern matching.
    The first pattern group to match wins (navigational > transactional >
    commercial > informational).  If nothing matches we fall back to
    'informational' because purely topical queries (e.g. "python programming")
    are most likely informational.
    """

    def classify(self, keyword: str) -> str:
        """
        Return the intent label for *keyword*.

        Args:
            keyword: A single keyword string.

        Returns:
            One of: 'informational', 'transactional', 'commercial', 'navigational'.
        """
        kw_lower = keyword.lower().strip()

        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(kw_lower):
                    return intent

        return DEFAULT_INTENT

    def classify_batch(self, keywords: list[str]) -> Dict[str, str]:
        """
        Classify a list of keywords at once.

        Returns:
            Dict mapping keyword → intent label.
        """
        return {kw: self.classify(kw) for kw in keywords}

    def get_intent_distribution(self, keywords: list[str]) -> Dict[str, int]:
        """
        Return a count of each intent across a keyword list.
        Useful for summary statistics in API responses.
        """
        dist: Dict[str, int] = {
            "informational": 0,
            "transactional": 0,
            "commercial": 0,
            "navigational": 0,
        }
        for kw in keywords:
            intent = self.classify(kw)
            dist[intent] = dist.get(intent, 0) + 1
        return dist
