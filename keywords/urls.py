from django.urls import path
from .views import KeywordResearchView, KeywordListView

urlpatterns = [
    path('keyword-research/', KeywordResearchView.as_view(), name='keyword-research'),
    path('keywords/', KeywordListView.as_view(), name='keyword-list'),
]
