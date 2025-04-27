from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileAllowed

class RegisterForm(FlaskForm):
    admin_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=100)])
    admin_email = StringField("Email", validators=[DataRequired(), Email()])
    admin_password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('admin_password')])
    admin_profile_pic = FileField("Profile Picture", validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField("Register")