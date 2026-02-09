from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Length

class EditProfileForm(FlaskForm):
    bio = TextAreaField("Bio", validators=[Length(max=280)])
    submit = SubmitField("Save")
