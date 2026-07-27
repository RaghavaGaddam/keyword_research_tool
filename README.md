# KeyLens — NLP Keyword Research Tool

A full-stack keyword research tool built with **Python**, **Django REST Framework**, and **NLP** (KeyBERT + SentenceTransformers + KMeans).

---

## Features

| Feature | Technology |
|---|---|
| Keyword idea generation | KeyBERT + template expansion |
| Semantic clustering | SentenceTransformers + KMeans (TF-IDF offline fallback) |
| Search intent classification | Rule-based regex classifier |
| Difficulty scoring | Heuristic scorer (0–100) |
| Caching | Django in-memory (swap for Redis in prod) |
| REST API | Django REST Framework |
| Frontend | Django template, dark-mode UI |
| Database | SQLite (dev) / any Django-supported DB |

---

## Project Structure

```
keyword_research_tool/
├── config/
│   ├── settings.py         # Django settings
│   ├── urls.py             # Root URL conf
│   └── wsgi.py
├── keywords/
│   ├── models.py           # Keyword + ResearchSession models
│   ├── serializers.py      # DRF serializers
│   ├── views.py            # API views
│   ├── urls.py             # App URL conf
│   ├── admin.py            # Django admin
│   └── services/
│       ├── keyword_generator.py   # KeyBERT / template expansion
│       ├── clustering.py          # SentenceTransformers + KMeans
│       ├── intent_classifier.py   # Rule-based intent classifier
│       └── difficulty_scorer.py   # Heuristic difficulty scorer
├── templates/
│   └── index.html          # Frontend UI
├── requirements.txt
└── manage.py
```

---

## Quick Start

### 1. Clone / enter the project

```bash
cd keyword_research_tool
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `keybert` and `sentence-transformers` will download the
> `all-MiniLM-L6-v2` model (~90 MB) on first use (requires internet).
> The tool works **fully offline** with TF-IDF fallback if the model
> cannot be downloaded.

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. (Optional) Create a superuser for the Django admin

```bash
python manage.py createsuperuser
```

### 6. Start the development server

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

---

## API Reference

### `POST /api/keyword-research/`

Generate keyword ideas, clusters, and intent data for a seed keyword.

**Request body (JSON):**

```json
{
  "seed_keyword": "python machine learning",
  "top_n": 25,
  "n_clusters": null
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `seed_keyword` | string | required | The topic to research |
| `top_n` | int | 25 | Max keywords to return (5–100) |
| `n_clusters` | int \| null | null | Override auto cluster count |

**Sample `curl` request:**

```bash
curl -X POST http://127.0.0.1:8000/api/keyword-research/ \
  -H "Content-Type: application/json" \
  -d '{"seed_keyword": "running shoes", "top_n": 20}'
```

**Response (200 OK):**

```json
{
  "seed_keyword": "running shoes",
  "keywords": [
    { "keyword": "best running shoes", "intent": "commercial", "difficulty_score": 60.0 },
    { "keyword": "how to choose running shoes", "intent": "informational", "difficulty_score": 20.0 },
    { "keyword": "buy running shoes online", "intent": "transactional", "difficulty_score": 60.0 }
  ],
  "clusters": {
    "0": ["best running shoes", "running shoes review", "top running shoes"],
    "1": ["buy running shoes online", "running shoes near me", "cheap running shoes"],
    "2": ["how to choose running shoes", "running shoes guide", "running shoes for beginners"]
  },
  "intent_distribution": {
    "informational": 9,
    "commercial": 6,
    "transactional": 4,
    "navigational": 1
  },
  "total_keywords": 20,
  "total_clusters": 3
}
```

---

### `GET /api/keywords/`

Retrieve stored keywords from the database.

**Query parameters:**

| Param | Description |
|---|---|
| `seed` | Filter by seed keyword (partial match) |
| `intent` | Filter by intent (`informational`, `transactional`, etc.) |

```bash
curl "http://127.0.0.1:8000/api/keywords/?seed=running&intent=commercial"
```

---

## Intent Classification Logic

| Intent | Signals |
|---|---|
| **Informational** | how to, what is, guide, tutorial, tips, learn |
| **Transactional** | buy, order, near me, discount, deal, free trial |
| **Commercial** | best, top, review, comparison, vs, worth it |
| **Navigational** | login, website, official, app, download |

---

## Production Notes

1. **Model caching** – SentenceTransformers caches the model in `~/.cache/huggingface/`. Pre-download with:
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```

2. **Swap SQLite → PostgreSQL** – Update `DATABASES` in `config/settings.py`.

3. **Redis caching** – Replace `LocMemCache` with:
   ```python
   CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": "redis://127.0.0.1:6379/1"}}
   ```

4. **Secret key** – Set `SECRET_KEY` via environment variable in production.

5. **Static files** – Run `python manage.py collectstatic` before deploying.
