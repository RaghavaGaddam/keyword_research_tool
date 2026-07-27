"""
Serializers for the Keyword Research API.
"""
from rest_framework import serializers
from .models import Keyword, ResearchSession


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = [
            'id',
            'text',
            'seed_keyword',
            'search_volume',
            'competition',
            'intent',
            'difficulty_score',
            'cluster_id',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class KeywordResearchRequestSerializer(serializers.Serializer):
    """Validates incoming keyword research requests."""

    seed_keyword = serializers.CharField(
        max_length=255,
        min_length=1,
        help_text="The topic or seed keyword to research.",
    )
    top_n = serializers.IntegerField(
        default=25,
        min_value=5,
        max_value=100,
        required=False,
        help_text="Maximum number of keyword ideas to return.",
    )
    n_clusters = serializers.IntegerField(
        default=None,
        min_value=2,
        max_value=10,
        required=False,
        allow_null=True,
        help_text="Override automatic cluster count.",
    )


class KeywordItemSerializer(serializers.Serializer):
    """One keyword entry in the API response."""

    keyword = serializers.CharField()
    intent = serializers.CharField()
    difficulty_score = serializers.FloatField()


class KeywordResearchResponseSerializer(serializers.Serializer):
    """Full API response structure."""

    seed_keyword = serializers.CharField()
    keywords = KeywordItemSerializer(many=True)
    clusters = serializers.DictField(child=serializers.ListField(child=serializers.CharField()))
    intent_distribution = serializers.DictField(child=serializers.IntegerField())
    total_keywords = serializers.IntegerField()
    total_clusters = serializers.IntegerField()
