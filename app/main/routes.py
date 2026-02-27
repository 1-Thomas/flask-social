from flask import render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.main import bp
from app.extensions import db
from app.models import Post, Comment
from app.main.forms import PostForm

from app.main.forms_profile import EditProfileForm
from flask import request, abort
from app.models import User, Message
from app.models import Like
from app.models import Comment
from app.main.forms_comment import CommentForm
from app.main.forms_message import MessageForm
from app.main.forms_post_edit import EditPostForm
import os
import uuid
from werkzeug.utils import secure_filename
POSTS_PER_PAGE = 10
POINTS_POST = 10
POINTS_COMMENT = 3
POINTS_LIKE = 1
POINTS_FOLLOW = 2
POINTS_MESSAGE = 1


@bp.route("/")
@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)

    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page,
        per_page=POSTS_PER_PAGE,
        error_out=False,
    )
    posts = pagination.items

    return render_template(
        "main/index.html",
        posts=posts,
        pagination=pagination,
        Comment=Comment,
    )

@bp.route("/post/new", methods=["GET", "POST"])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user)
        db.session.add(post)
        current_user.add_points(POINTS_POST)
        db.session.commit()
        flash("Posted.")
        return redirect(url_for("main.index"))
    return render_template("main/create_post.html", form=form)

@bp.route("/u/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)

    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page,
        per_page=POSTS_PER_PAGE,
        error_out=False,
    )
    posts = pagination.items

    return render_template(
        "main/profile.html",
        profile_user=user,
        posts=posts,
        pagination=pagination,
        Comment=Comment,
    )


@bp.route("/settings/profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.bio = form.bio.data or ""
        db.session.commit()
        flash("Profile updated.")
        return redirect(url_for("main.profile", username=current_user.username))

    if form.bio.data is None:
        form.bio.data = current_user.bio

    return render_template("main/edit_profile.html", form=form)

@bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()

    if user.id == current_user.id:
        flash("You cannot follow yourself.")
        return redirect(url_for("main.profile", username=username))

   
    if not current_user.is_following(user):
        current_user.follow(user)
        current_user.add_points(POINTS_FOLLOW)
        db.session.commit()

    return redirect(url_for("main.profile", username=username))

@bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user.id == current_user.id:
        flash("You cannot unfollow yourself.")
        return redirect(url_for("main.profile", username=username))

    current_user.unfollow(user)
    db.session.commit()
    return redirect(url_for("main.profile", username=username))

@bp.route("/following")
@login_required
def following_feed():
    page = request.args.get("page", 1, type=int)

    followed_ids = [u.id for u in current_user.followed.all()] + [current_user.id]

    pagination = Post.query.filter(Post.user_id.in_(followed_ids)) \
        .order_by(Post.timestamp.desc()) \
        .paginate(page=page, per_page=POSTS_PER_PAGE, error_out=False)

    posts = pagination.items

    return render_template(
        "main/following_feed.html",
        posts=posts,
        pagination=pagination,
        Comment=Comment,
    )

@bp.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)

    existing = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing is None:
        db.session.add(Like(user_id=current_user.id, post_id=post.id))
        current_user.add_points(POINTS_LIKE)
        db.session.commit()

    return redirect(request.referrer or url_for("main.index"))

@bp.route("/unlike/<int:post_id>", methods=["POST"])
@login_required
def unlike_post(post_id):
    post = Post.query.get_or_404(post_id)

    existing = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing is not None:
        db.session.delete(existing)
        db.session.commit()

    return redirect(request.referrer or url_for("main.index"))

@bp.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, author=current_user, post=post)
        db.session.add(comment)
        current_user.add_points(POINTS_COMMENT)
        db.session.commit()

    return redirect(request.referrer or url_for("main.index"))

@bp.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author.id != current_user.id:
        abort(403)

    form = EditPostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.commit()
        flash("Post updated.")
        return redirect(url_for("main.index"))

    if form.body.data is None:
        form.body.data = post.body

    return render_template("main/edit_post.html", form=form, post=post)

@bp.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author.id != current_user.id:
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.")
    return redirect(request.referrer or url_for("main.index"))

@bp.route("/search")
def search():
    q = (request.args.get("q") or "").strip()
    users = []
    posts = []

    if q:
        users = (
            User.query
            .filter(User.username.ilike(f"%{q}%"))
            .order_by(User.username.asc())
            .all()
        )
        posts = (
            Post.query
            .filter(Post.body.ilike(f"%{q}%"))
            .order_by(Post.timestamp.desc())
            .all()
        )

    return render_template("main/search.html", q=q, users=users, posts=posts)


@bp.route("/messages")
@login_required
def inbox():
    msgs = (
        Message.query
        .filter((Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id))
        .order_by(Message.timestamp.desc())
        .all()
    )

    latest_by_user = {}
    for m in msgs:
        other_id = m.recipient_id if m.sender_id == current_user.id else m.sender_id
        if other_id not in latest_by_user:
            latest_by_user[other_id] = m

    others = User.query.filter(User.id.in_(latest_by_user.keys())).all() if latest_by_user else []
    other_map = {u.id: u for u in others}

    threads = []
    for other_id, last_msg in latest_by_user.items():
        other_user = other_map.get(other_id)
        if other_user:
            threads.append((other_user, last_msg))

    threads.sort(key=lambda t: t[1].timestamp, reverse=True)

   
    all_users = User.query.filter(User.id != current_user.id).order_by(User.username.asc()).all()

    return render_template(
        "main/inbox.html",
        threads=threads,
        all_users=all_users
    )

@bp.route("/messages/u/<username>", methods=["GET", "POST"])
@login_required
def thread(username):
    other = User.query.filter_by(username=username).first_or_404()

    if other.id == current_user.id:
        abort(400)

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(
            sender_id=current_user.id,
            recipient_id=other.id,
            body=form.body.data
        )
        db.session.add(msg)

       
        current_user.add_points(POINTS_MESSAGE)

        db.session.commit()
        return redirect(url_for("main.thread", username=other.username))

    messages = (
        Message.query
        .filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == other.id)) |
            ((Message.sender_id == other.id) & (Message.recipient_id == current_user.id))
        )
        .order_by(Message.timestamp.asc())
        .all()
    )

    unread = [
        m for m in messages
        if (m.recipient_id == current_user.id and not m.is_read)
    ]

    if unread:
        for m in unread:
            m.is_read = True
        db.session.commit()

    return render_template(
        "main/thread.html",
        other=other,
        messages=messages,
        form=form
    )


@bp.route("/messages/new/<username>", methods=["GET", "POST"])
@login_required
def new_message(username):
    other = User.query.filter_by(username=username).first_or_404()
    if other.id == current_user.id:
        abort(400)

    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(sender_id=current_user.id, recipient_id=other.id, body=form.body.data)
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for("main.thread", username=other.username))

    return render_template("main/new_message.html", other=other, form=form)

def save_image(uploaded_file):
    if not uploaded_file or not uploaded_file.filename:
        return None

    filename = secure_filename(uploaded_file.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return None

    new_name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], new_name)
    uploaded_file.save(path)
    return new_name