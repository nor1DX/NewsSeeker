import feedparser
from datetime import datetime, timezone

from models import db, Post

FEEDS = {
    "Lenta.ru": "https://lenta.ru/rss",
    "RIA Novosti": "https://ria.ru/export/rss2/world/index.xml",
    "Kommersant": "https://www.kommersant.ru/RSS/news.xml",
    "TASS": "https://tass.ru/rss/v2.xml",
    "RBC": "https://www.rbc.ru/v10/news.rss",
}


def _summary(entry):
    if hasattr(entry, "summary"):
        return entry.summary
    if hasattr(entry, "description"):
        return entry.description
    return ""


def refresh_feeds():
    """Парсим RSS и кладём новые записи в базу."""
    for source, url in FEEDS.items():
        data = feedparser.parse(url)
        for entry in data.entries:
            if Post.query.filter_by(link=entry.link).first():
                continue  # уже есть
            title = entry.title
            summary = _summary(entry)
            ts = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
            if ts:
                published = datetime(*ts[:6], tzinfo=timezone.utc)
            else:
                published = datetime.now(timezone.utc)
            post = Post(
                title=title,
                summary=summary,
                link=entry.link,
                published=published,
                source=source,
            )
            db.session.add(post)
        db.session.commit()
