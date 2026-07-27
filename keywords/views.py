"""
API Views for the Keyword Research Tool.
"""
import hashlib
import logging

from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Keyword, ResearchSession
from .serializers import KeywordResearchRequestSerializer
from .services import KeywordGeneratorService, KeywordClusteringService, IntentClassifierService
from .services.difficulty_scorer import DifficultyScorer

logger = logging.getLogger(__name__)

_generator = KeywordGeneratorService()
_clusterer = KeywordClusteringService()
_classifier = IntentClassifierService()
_scorer = DifficultyScorer()


def _cache_key(seed, top_n, n_clusters):
    raw = f"{seed}:{top_n}:{n_clusters}"
    return "kw_research:" + hashlib.md5(raw.encode()).hexdigest()


class KeywordResearchView(APIView):
    """POST /api/keyword-research/"""

    def post(self, request):
        req_serializer = KeywordResearchRequestSerializer(data=request.data)
        if not req_serializer.is_valid():
            return Response({"errors": req_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        seed = req_serializer.validated_data["seed_keyword"].strip().lower()
        top_n = req_serializer.validated_data.get("top_n", 25)
        n_clusters = req_serializer.validated_data.get("n_clusters")

        cache_key = _cache_key(seed, top_n, n_clusters)
        cached = cache.get(cache_key)
        if cached:
            logger.info("Cache hit for seed=%s", seed)
            return Response(cached, status=status.HTTP_200_OK)

        try:
            keywords = _generator.generate(seed, top_n=top_n)
            if not keywords:
                return Response({"error": "Could not generate keywords."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            intent_map = _classifier.classify_batch(keywords)
            difficulty_map = _scorer.score_batch(keywords)
            clusters = _clusterer.cluster(keywords, n_clusters=n_clusters)
            intent_dist = _classifier.get_intent_distribution(keywords)

        except Exception as exc:
            logger.exception("NLP pipeline error for seed=%s", seed)
            return Response({"error": f"NLP processing failed: {str(exc)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            self._persist(seed, keywords, intent_map, difficulty_map, clusters)
        except Exception:
            logger.warning("DB persistence failed for seed=%s", seed, exc_info=True)

        keyword_items = [
            {"keyword": kw, "intent": intent_map[kw], "difficulty_score": difficulty_map[kw]}
            for kw in keywords
        ]

        response_data = {
            "seed_keyword": seed,
            "keywords": keyword_items,
            "clusters": clusters,
            "intent_distribution": intent_dist,
            "total_keywords": len(keywords),
            "total_clusters": len(clusters),
        }

        cache.set(cache_key, response_data)
        return Response(response_data, status=status.HTTP_200_OK)

    @staticmethod
    def _persist(seed, keywords, intent_map, difficulty_map, clusters):
        keyword_cluster = {}
        for cluster_id, kws in clusters.items():
            for kw in kws:
                keyword_cluster[kw] = int(cluster_id)

        kw_objects = []
        for kw in keywords:
            obj, _ = Keyword.objects.update_or_create(
                text=kw,
                defaults={
                    "seed_keyword": seed,
                    "intent": intent_map.get(kw, "informational"),
                    "difficulty_score": difficulty_map.get(kw),
                    "cluster_id": keyword_cluster.get(kw),
                },
            )
            kw_objects.append(obj)

        session = ResearchSession.objects.create(
            seed_keyword=seed,
            total_keywords=len(keywords),
            total_clusters=len(clusters),
        )
        session.keywords.set(kw_objects)


class KeywordListView(APIView):
    """GET /api/keywords/"""

    def get(self, request):
        from .serializers import KeywordSerializer
        seed = request.query_params.get("seed")
        intent = request.query_params.get("intent")
        qs = Keyword.objects.all()
        if seed:
            qs = qs.filter(seed_keyword__icontains=seed)
        if intent:
            qs = qs.filter(intent=intent)
        return Response(KeywordSerializer(qs[:200], many=True).data)
