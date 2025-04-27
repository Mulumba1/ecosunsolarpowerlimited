from flask_wtf import FlaskForm
from wtforms import StringField,  SubmitField, TextAreaField, SelectField, DecimalField
from wtforms.validators import DataRequired

from flask_wtf.file import MultipleFileField, FileAllowed, FileRequired

class ProductForm(FlaskForm):
    name = StringField("Product name", validators=[DataRequired()])
    category = SelectField("Product Category", coerce=int, validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    images = MultipleFileField("Choose Files", validators=[
    FileAllowed(["jpg", "jpeg", "png"], "Images only!")])

    submit = SubmitField('Add Product')