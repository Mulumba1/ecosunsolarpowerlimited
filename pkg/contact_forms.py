from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,EmailField, TextAreaField
from wtforms.validators import DataRequired,Email


class InitialCapitalStringField(StringField):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0].strip().title()
        else:
            self.data = ''




class ContactForm(FlaskForm):
    name = InitialCapitalStringField('Name', render_kw={"placeholder": "Enter your Full Name"}, validators=[DataRequired()])
    email = EmailField('Email', render_kw={"placeholder": "Enter your email"},validators=[DataRequired()])
    phone = StringField('Phone Number', render_kw={"placeholder": "Enter your phone number"}, validators=[DataRequired()])
    subject = StringField('Subject', render_kw={"placeholder": "Subject"}, validators=[DataRequired()])

    message = TextAreaField('Message',render_kw={"placeholder":"Type your message","rows": "10",}, validators=[DataRequired()])
    submit = SubmitField('Send Message')