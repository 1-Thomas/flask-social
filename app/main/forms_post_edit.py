from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class EditPostForm(FlaskForm):
    body = TextAreaField("Edit post", validators=[DataRequired(), Length(max=280)])
    submit = SubmitField("Save")
