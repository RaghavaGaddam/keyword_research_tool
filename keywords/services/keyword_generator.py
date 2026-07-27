"""
Keyword Generation Service
Generates keyword ideas from a seed keyword using:
  1. SentenceTransformers/KeyBERT (when model available)
  2. TF-IDF + template expansion fallback (always works offline)
"""
import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Modifier templates (PASA-style expansions)
# ---------------------------------------------------------------------------
MODIFIER_TEMPLATES = {
    "question": [
        "how to {kw}", "what is {kw}", "why {kw}", "when to {kw}",
        "where to {kw}", "who needs {kw}", "how does {kw} work",
    ],
    "commercial": [
        "best {kw}", "top {kw}", "{kw} review", "{kw} comparison",
        "{kw} vs alternatives", "cheap {kw}", "affordable {kw}",
        "{kw} price", "{kw} cost", "{kw} worth it",
    ],
    "transactional": [
        "buy {kw}", "{kw} online", "{kw} near me", "{kw} for sale",
        "{kw} discount", "{kw} deal", "{kw} coupon", "{kw} free trial",
    ],
    "informational": [
        "{kw} guide", "{kw} tutorial", "{kw} tips", "{kw} examples",
        "{kw} definition", "{kw} meaning", "learn {kw}",
        "{kw} for beginners", "{kw} explained", "{kw} overview",
        "{kw} basics", "{kw} introduction", "{kw} benefits",
        "{kw} advantages", "{kw} use cases",
    ],
    "navigational": [
        "{kw} website", "{kw} login", "{kw} official site",
        "{kw} app", "{kw} download",
    ],
    "long_tail": [
        "{kw} for small business", "{kw} step by step",
        "how to start {kw}", "{kw} course", "{kw} certification",
        "best free {kw}", "{kw} tools", "{kw} software",
        "{kw} training", "{kw} skills",
    ],
}


def _try_load_keybert(model_name: str):
    """Attempt to load KeyBERT; return None if unavailable."""
    try:
        from keybert import KeyBERT
        model = KeyBERT(model_name)
        logger.info("KeyBERT loaded successfully with %s", model_name)
        return model
    except Exception as e:
        logger.warning("KeyBERT unavailable (%s); using template-only mode.", e)
        return None


class KeywordGeneratorService:
    """
    Generates semantically related keyword ideas from a seed keyword.

    Two modes:
      • Full NLP mode  – KeyBERT + SentenceTransformers (requires model download)
      • Template mode  – Pure template expansion + TF-IDF ranking (offline-safe)
    """

    _model = None          # KeyBERT instance or None
    _model_loaded = False  # Tracks whether we've tried to load yet

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name

    @property
    def model(self):
        if not KeywordGeneratorService._model_loaded:
            KeywordGeneratorService._model = _try_load_keybert(self.model_name)
            KeywordGeneratorService._model_loaded = True
        return KeywordGeneratorService._model

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate(self, seed_keyword: str, top_n: int = 30) -> List[str]:
        """
        Generate keyword ideas for *seed_keyword*.
        Falls back to template-only generation if NLP models are unavailable.
        """
        seed = seed_keyword.strip().lower()

        # Build all template expansions (always available)
        template_keywords = self._template_expand(seed)

        if self.model is not None:
            try:
                return self._generate_with_keybert(seed, template_keywords, top_n)
            except Exception as e:
                logger.warning("KeyBERT inference failed (%s); using template fallback.", e)

        # Fallback: template expansion + TF-IDF style ranking
        return self._generate_template_only(seed, template_keywords, top_n)

    # ------------------------------------------------------------------
    # NLP mode
    # ------------------------------------------------------------------

    def _generate_with_keybert(
        self, seed: str, template_keywords: List[str], top_n: int
    ) -> List[str]:
        corpus = "\n".join([seed] + template_keywords)
        raw: List[Tuple[str, float]] = self.model.extract_keywords(
            corpus,
            keyphrase_ngram_range=(1, 4),
            stop_words="english",
            top_n=top_n * 2,
            use_mmr=True,
            diversity=0.5,
        )
        extracted = [kw for kw, _ in raw]
        combined = extracted + template_keywords
        return self._clean_and_deduplicate(seed, combined, top_n)

    # ------------------------------------------------------------------
    # Template-only fallback (offline-safe)
    # ------------------------------------------------------------------

    def _generate_template_only(
        self, seed: str, template_keywords: List[str], top_n: int
    ) -> List[str]:
        """
        Rank template-expanded keywords by a heuristic:
        longer phrases (more specific) and those containing the full seed
        are ranked higher. This approximates long-tail relevance.
        """
        def heuristic_score(kw: str) -> float:
            words = kw.split()
            length_bonus = min(len(words) * 0.2, 1.0)
            seed_bonus = 0.5 if seed in kw else 0.0
            return length_bonus + seed_bonus

        scored = sorted(template_keywords, key=heuristic_score, reverse=True)
        return self._clean_and_deduplicate(seed, scored, top_n)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _template_expand(self, seed: str) -> List[str]:
        result = []
        for templates in MODIFIER_TEMPLATES.values():
            for tpl in templates:
                result.append(tpl.format(kw=seed))
        # Add single-word variants for multi-word seeds
        words = seed.split()
        if len(words) > 1:
            for word in words:
                if len(word) > 3:
                    result.extend(t.format(kw=word) for templates in MODIFIER_TEMPLATES.values() for t in templates[:3])
        return result

    @staticmethod
    def _clean_and_deduplicate(seed: str, keywords: List[str], top_n: int) -> List[str]:
        seen, cleaned = set(), []
        for kw in keywords:
            kw = re.sub(r"[^\w\s\-]", "", kw).strip().lower()
            if kw and kw != seed and len(kw) > 2 and kw not in seen:
                seen.add(kw)
                cleaned.append(kw)
            if len(cleaned) >= top_n:
                break
        return cleaned
