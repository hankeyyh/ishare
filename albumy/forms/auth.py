# coding: utf-8

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length, Email, ValidationError, Regexp, EqualTo
from albumy.models import User


class RegisterForm(FlaskForm):
	"""注册"""
	name = StringField("Name", validators=[DataRequired(), Length(1, 30)])
	email = StringField("Email", validators=[DataRequired(), Length(1, 254), Email()])
	username = StringField("UserName", validators=[DataRequired(), Length(1, 20),
	                                               Regexp('^[a-zA-Z0-9]*$',
	                                                      message='The username should contain only a-z, A-Z and 0-9.')
	                                               ])
	password = PasswordField("Password", validators=[DataRequired(), Length(8, 128), EqualTo('password2')])
	password2 = PasswordField("Confirm password", validators=[DataRequired()])
	submit = SubmitField()
	
	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError("UserName already been used!")
	
	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError("Email already been used!")


class LoginForm(FlaskForm):
	"""登录"""
	email = StringField("Email", validators=[DataRequired(), Length(1, 254), Email()])
	password = PasswordField("Password", validators=[DataRequired()])
	remember_me = BooleanField("remember me")
	submit = SubmitField("Login")
	
	
class ForgetPasswordForm(FlaskForm):
	"""忘记密码"""
	email = StringField("Email", validators=[DataRequired(), Length(1, 254), Email()])
	submit = SubmitField()
	

class ResetPasswordForm(FlaskForm):
	"""重置密码"""
	email = StringField("Email", validators=[DataRequired(), Length(1, 254), Email()])
	password = PasswordField("Password", validators=[DataRequired(), Length(8, 128), EqualTo('password2')])
	password2 = PasswordField("Confirm password", validators=[DataRequired()])
	submit = SubmitField()