"""
Keyword Clustering Service
Groups keywords by semantic similarity using SentenceTransformers + KMeans.
Falls back to TF-IDF vectorisation when the neural model is unavailable.
"""
import math
import logging
from typing import Dict, List, Optional

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

logger = logging.getLogger(__name__)


def _try_load_sentence_transformer(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        logger.info("SentenceTransformer loaded: %s", model_name)
        return model
    except Exception as e:
        logger.warning("SentenceTransformer unavailable (%s); TF-IDF fallback active.", e)
        return None


class KeywordClusteringService:
    """
    Clusters keywords into semantically similar groups.

    Full mode:  SentenceTransformer embeddings + KMeans
    Fallback:   TF-IDF vectors + KMeans (fully offline)
    """

    _st_model = None
    _st_model_loaded = False

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name

    @property
    def st_model(self):
        if not KeywordClusteringService._st_model_loaded:
            KeywordClusteringService._st_model = _try_load_sentence_transformer(self.model_name)
            KeywordClusteringService._st_model_loaded = True
        return KeywordClusteringService._st_model

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def cluster(
        self,
        keywords: List[str],
        n_clusters: Optional[int] = None,
    ) -> Dict[str, List[str]]:
        if len(keywords) < 2:
            return {"0": keywords}

        embeddings = self._encode(keywords)
        k = n_clusters or self._auto_k(embeddings, len(keywords))
        labels = self._run_kmeans(embeddings, k)
        return self._build_clusters(keywords, labels)

    # ------------------------------------------------------------------
    # Encoding (neural or TF-IDF)
    # ------------------------------------------------------------------

    def _encode(self, keywords: List[str]) -> np.ndarray:
        if self.st_model is not None:
            try:
                return self.st_model.encode(keywords, show_progress_bar=False)
            except Exception as e:
                logger.warning("ST encode failed (%s); using TF-IDF.", e)
        return self._tfidf_encode(keywords)

    @staticmethod
    def _tfidf_encode(keywords: List[str]) -> np.ndarray:
        """TF-IDF character n-gram vectors – a solid offline substitute."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=512)
        matrix = vec.fit_transform(keywords)
        return matrix.toarray()

    # ------------------------------------------------------------------
    # Cluster count selection
    # ------------------------------------------------------------------

    def _auto_k(self, embeddings: np.ndarray, n: int) -> int:
        if n < 4:
            return min(2, n)
        max_k = min(8, int(math.sqrt(n)))
        if max_k < 2:
            return 2

        best_k, best_score = 2, -1.0
        for k in range(2, max_k + 1):
            labels = self._run_kmeans(embeddings, k)
            try:
                score = silhouette_score(embeddings, labels)
                if score > best_score:
                    best_score, best_k = score, k
            except Exception:
                pass
        return best_k

    # ------------------------------------------------------------------
    # KMeans + cluster building
    # ------------------------------------------------------------------

    @staticmethod
    def _run_kmeans(embeddings: np.ndarray, k: int) -> np.ndarray:
        km = KMeans(n_clusters=k, random_state=42, n_init="auto")
        return km.fit_predict(embeddings)

    @staticmethod
    def _build_clusters(
        keywords: List[str], labels: np.ndarray
    ) -> Dict[str, List[str]]:
        clusters: Dict[str, List[str]] = {}
        for kw, label in zip(keywords, labels):
            key = str(label)
            clusters.setdefault(key, []).append(kw)
        return clusters
