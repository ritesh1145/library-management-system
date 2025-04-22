from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, TelField, SelectField, TextAreaField, DateField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, Optional

class MemberForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    phone = TelField('Phone Number', validators=[Optional()])
    membership_type = SelectField('Membership Type', 
                               choices=[('student', 'Student'), 
                                       ('faculty', 'Faculty'),
                                       ('standard', 'Standard'),
                                       ('premium', 'Premium')],
                               validators=[DataRequired()])
    address = TextAreaField('Address', validators=[Optional()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()], format='%Y-%m-%d')
    id_proof = FileField('ID Proof')
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    agree_terms = BooleanField('I agree to the terms and conditions', validators=[DataRequired()])

class LoanForm(FlaskForm):
    member_id = SelectField('Member', validators=[DataRequired()], coerce=int)
    book_id = SelectField('Book', validators=[DataRequired()], coerce=int)
    issue_date = DateField('Issue Date', validators=[DataRequired()], format='%Y-%m-%d')
    due_date = DateField('Due Date', validators=[DataRequired()], format='%Y-%m-%d')
    notes = TextAreaField('Notes', validators=[Optional()]) 