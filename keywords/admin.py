from django.contrib import admin
from .models import Keyword, ResearchSession

@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ['text', 'intent', 'difficulty_score', 'cluster_id', 'seed_keyword', 'created_at']
    list_filter = ['intent', 'seed_keyword']
    search_fields = ['text', 'seed_keyword']

@admin.register(ResearchSession)
class ResearchSessionAdmin(admin.ModelAdmin):
    list_display = ['seed_keyword', 'total_keywords', 'total_clusters', 'created_at']
    list_filter = ['seed_keyword']
