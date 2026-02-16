from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.main import bp
from app.extensions import db
from app.models import Post, Comment
from app.main.forms import PostForm
from app.models import User
from app.main.forms_profile import EditProfileForm
from flask import request
from app.models import User
from app.models import Like
from app.models import Comment
from app.main.forms_comment import CommentForm
from flask import abort
from app.main.forms_post_edit import EditPostForm


@bp.route("/")
def index():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("main/index.html", posts=posts, Comment=Comment)

@bp.route("/post/new", methods=["GET", "POST"])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Posted.")
        return redirect(url_for("main.index"))
    return render_template("main/create_post.html", form=form)

@bp.route("/u/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template("main/profile.html", profile_user=user, posts=posts, Comment=Comment)


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

    current_user.follow(user)
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

    followed_ids = [u.id for u in current_user.followed.all()] + [current_user.id]
    posts = Post.query.filter(Post.user_id.in_(followed_ids)).order_by(Post.timestamp.desc()).all()
    return render_template("main/following_feed.html", posts=posts, Comment=Comment)

@bp.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)

    existing = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing is None:
        db.session.add(Like(user_id=current_user.id, post_id=post.id))
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
