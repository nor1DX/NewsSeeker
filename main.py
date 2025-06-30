import os
import datetime as dt
import math
from flask import g
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from models import db, Post, init_db
from fetcher import refresh_feeds


from flask import (Flask, render_template, request,
                   jsonify, redirect, url_for, session)
from models import db, Post, init_db
from fetcher import refresh_feeds

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL",
                                                  "sqlite:///database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("SECRET_KEY", "change-me-please")

db.init_app(app)

# --- инициализация ---
with app.app_context():
    init_db()
    refresh_feeds()
    _last_refresh = dt.datetime.utcnow()

REFRESH_INTERVAL = 15  # минут
PAGE_SIZE = 5


def maybe_refresh():
    """Обновляем RSS раз в REFRESH_INTERVAL минут."""
    global _last_refresh
    now = dt.datetime.utcnow()
    if (now - _last_refresh).total_seconds() > REFRESH_INTERVAL * 60:
        refresh_feeds()
        _last_refresh = now


# ---------- публичные маршруты ----------
@app.route("/")
def index():
    maybe_refresh()
    source = request.args.get("source") or None
    page = int(request.args.get("page", 1))

    query = Post.query
    if source:
        query = query.filter_by(source=source)

    total = query.count()
    posts = (query.order_by(Post.published.desc())
             .offset((page - 1) * PAGE_SIZE)
             .limit(PAGE_SIZE)
             .all())

    # уникальные источники для фильтра
    sources = [row[0] for row in db.session.query(Post.source).distinct().all()]

    return render_template(
        "index.html",
        posts=posts,
        page=page,
        total_pages=math.ceil(total / PAGE_SIZE),
        sources=sources,
        current_source=source,
    )


@app.route("/api/posts")
def api_posts():
    """Возвращает новости пачкой в JSON для кнопки «Показать ещё»."""
    maybe_refresh()
    source = request.args.get("source") or None
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", PAGE_SIZE))

    query = Post.query
    if source:
        query = query.filter_by(source=source)

    posts = (query.order_by(Post.published.desc())
             .offset(offset)
             .limit(limit)
             .all())

    return jsonify([
        {
            "id": p.id,
            "title": p.title,
            "summary": p.summary or "",
            "link": p.link,
            "published": p.published.isoformat(),
            "source": p.source,
        } for p in posts
    ])

@app.context_processor
def inject_globals():
    sources = [row[0] for row in db.session.query(Post.source).distinct().all()]
    return dict(
        sources=sources,
        is_admin=session.get("admin", False)
    )

def is_admin():
    return session.get("admin", False)
# ---------- простая админка ----------
def is_admin():
    return session.get("admin")


@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if password == os.getenv("ADMIN_PASSWORD", "admin"):
        session['admin'] = True
        return redirect(url_for('index'))
    else:
        session.pop('admin', None)
        return redirect(url_for('index', login_failed=1))



@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


@app.route("/admin")
def admin_panel():
    if not is_admin():
        return redirect(url_for("admin_login"))
    posts = Post.query.order_by(Post.published.desc()).all()
    return render_template("admin.html", posts=posts)


@app.post("/admin/delete/<int:post_id>")
def admin_delete(post_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("admin_panel"))


@app.route("/admin/edit/<int:post_id>", methods=["GET", "POST"])
def admin_edit(post_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    post = Post.query.get_or_404(post_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        summary = request.form.get("summary", "").strip()
        link = request.form.get("link", "").strip()
        source = request.form.get("source", "").strip()

        if not title or not link or not source:
            return render_template("edit.html", post=post, error="Все поля кроме текста обязательны.")

        post.title = title
        post.summary = summary
        post.link = link
        post.source = source
        db.session.commit()
        return redirect(url_for("admin_panel"))

    return render_template("edit.html", post=post)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
