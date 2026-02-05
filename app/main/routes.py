from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.main import bp
from app.extensions import db
from app.models import Post
from app.main.forms import PostForm

@bp.route("/")
def index():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("main/index.html", posts=posts)

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
