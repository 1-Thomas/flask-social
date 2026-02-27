from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed

class PostForm(FlaskForm):
    body = TextAreaField("What's do you want to post?", validators=[DataRequired(), Length(max=280)])
    submit = SubmitField("Post")
    
    image = FileField(
        "Image",
        validators=[FileAllowed(["jpg", "jpeg", "png", "gif"], "Images only!")]
    )
