from django.db import models


class Keyword(models.Model):
    """Model to store analysed keywords and their metadata."""

    INTENT_CHOICES = [
        ('informational', 'Informational'),
        ('transactional', 'Transactional'),
        ('commercial', 'Commercial'),
        ('navigational', 'Navigational'),
    ]

    text = models.CharField(max_length=500, unique=True, db_index=True)
    seed_keyword = models.CharField(max_length=255, blank=True, db_index=True)
    search_volume = models.IntegerField(null=True, blank=True)
    competition = models.FloatField(null=True, blank=True, help_text="0.0 (low) to 1.0 (high)")
    intent = models.CharField(max_length=20, choices=INTENT_CHOICES, default='informational')
    difficulty_score = models.FloatField(null=True, blank=True, help_text="0–100 difficulty score")
    cluster_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Keyword'
        verbose_name_plural = 'Keywords'

    def __str__(self):
        return f"{self.text} ({self.intent})"


class ResearchSession(models.Model):
    """Tracks a full keyword research session for a given seed keyword."""

    seed_keyword = models.CharField(max_length=255, db_index=True)
    keywords = models.ManyToManyField(Keyword, related_name='sessions', blank=True)
    total_keywords = models.IntegerField(default=0)
    total_clusters = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session: {self.seed_keyword} ({self.created_at.date()})"
