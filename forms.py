from flask_wtf import Form
from wtforms import TextField, PasswordField, StringField
from wtforms.validators import DataRequired, EqualTo, Length

# Set your classes here.


class RegisterForm(Form):
    cgid = StringField(
        'ID', validators=[DataRequired(), Length(min=6, max=25)]
    )
    name = StringField(
        'Username', validators=[DataRequired(), Length(min=6, max=25)]
    )
    cgrank = StringField(
        'Rank', validators=[DataRequired(), Length(min=6, max=25)]
    )
    password = PasswordField(
        'Password', validators=[DataRequired(), Length(min=6, max=40)]
    )
    confirm = PasswordField(
        'Repeat Password',
        [DataRequired(),
        EqualTo('password', message='Passwords must match')]
    )


class LoginForm(Form):
    uid = StringField('Username', [DataRequired()])
    sessdata = StringField('Username', [DataRequired()])
    csrf = StringField('Password', [DataRequired()])
    tagid = StringField('Username', [DataRequired()])


class ForgotForm(Form):
    email = TextField(
        'Email', validators=[DataRequired(), Length(min=6, max=40)]
    )
