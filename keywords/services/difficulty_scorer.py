"""
Keyword Difficulty Scoring Service
Provides a heuristic difficulty score (0–100) for each keyword.

In a production system this would call an SEO data provider API (Ahrefs, SEMrush, Moz).
Here we compute a transparent heuristic based on:
  - Word count (longer-tail = lower difficulty)
  - Presence of high-competition commercial modifiers
  - Presence of transactional intent signals (generally higher competition)
  - Whether the seed keyword itself appears in the phrase
"""

import re
from typing import List, Dict

# High-competition commercial terms increase the score
HIGH_COMPETITION_TERMS = re.compile(
    r"\b(best|top|review|buy|cheap|affordable|near me|vs|comparison|price)\b",
    re.I,
)

# Question-based keywords are typically lower competition
QUESTION_TERMS = re.compile(
    r"\b(how to|what is|why|when|where|who|tutorial|guide|tips|learn)\b",
    re.I,
)


class DifficultyScorer:
    """
    Heuristic-based keyword difficulty scorer.

    Score breakdown (adds up to 100 max):
      40 pts  – base difficulty (single/two-word keywords are hard)
      30 pts  – commercial/transactional intent penalty
     -20 pts  – long-tail reduction (≥4 words)
     -15 pts  – question modifier reduction
    """

    def score(self, keyword: str) -> float:
        """Return a 0–100 difficulty estimate for *keyword*."""
        words = keyword.strip().split()
        word_count = len(words)

        # Base difficulty: shorter = harder to rank for
        if word_count == 1:
            base = 80
        elif word_count == 2:
            base = 65
        elif word_count == 3:
            base = 50
        else:
            base = 35  # long-tail

        # Boost for high-competition commercial signals
        if HIGH_COMPETITION_TERMS.search(keyword):
            base = min(100, base + 10)

        # Reduction for informational question keywords
        if QUESTION_TERMS.search(keyword):
            base = max(0, base - 15)

        return round(float(base), 1)

    def score_batch(self, keywords: List[str]) -> Dict[str, float]:
        """Return {keyword: score} for a list of keywords."""
        return {kw: self.score(kw) for kw in keywords}
