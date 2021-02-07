# coding: utf-8

from flask import Blueprint, render_template, redirect, url_for, request, flash
from albumy import RegisterForm, LoginForm, db
from flask_login import login_user, logout_user, current_user, login_required

from albumy.emails import send_confirm_email, send_reset_password_email
from albumy.forms.auth import ForgetPasswordForm, ResetPasswordForm
from albumy.models import User
from albumy.settings import Operations
from albumy.utils import redirect_back, generate_token, validate_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))

	reg_form = RegisterForm()
	if reg_form.validate_on_submit():
		name = reg_form.name.data
		email = reg_form.email.data.lower()
		username = reg_form.username.data
		password = reg_form.password.data
		user = User(name=name, email=email, username=username)
		user.set_password(password)
		db.session.add(user)
		db.session.commit()
		token = generate_token(user, Operations.CONFIRM)
		send_confirm_email(user, token)
		flash('Confirm email sent, check your inbox.', 'info')
		return redirect(url_for('.login'))
	return render_template('auth/register.html', form=reg_form)


@auth_bp.route('/confirm/<token>')
@login_required
def confirm(token):
	if current_user.confirmed:
		return redirect(url_for('main.index'))
	
	if validate_token(user=current_user, token=token, operation=Operations.CONFIRM):
		flash('Account confirmed.', 'success')
		return redirect(url_for('main.index'))
	else:
		flash('Invalid or expired token.', 'danger')
		return redirect(url_for('.resend_confirm_email'))
		
@auth_bp.route('/resend-confirm-email')
def resend_confirm_email():
	if current_user.confirmed:
		return redirect(url_for('main.index'))
	
	token = generate_token(current_user, Operations.CONFIRM)
	send_confirm_email(current_user, token)
	flash('New email sent, check your inbox.', 'info')
	return redirect(url_for('main.index'))
	

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
		
	login_form = LoginForm()
	if login_form.validate_on_submit():
		email = login_form.email.data.lower()
		password = login_form.password.data
		user = User.query.filter_by(email=email).first()
		if user and user.validate_password(password):
			login_user(user, login_form.remember_me.data)
			return redirect_back()
		flash('Invalid email or password.', 'warning')
	return render_template('auth/login.html', form=login_form)


@auth_bp.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('main.index'))

@auth_bp.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	
	form = ForgetPasswordForm()
	if form.validate_on_submit():
		email = form.email.data.lower()
		user = User.query.filter_by(email=email).first()
		if user:
			token = generate_token(user, Operations.RESET_PASSWORD)
			send_reset_password_email(user, token)
			flash('Password reset email sent, check your inbox.', 'info')
			return redirect(url_for('.login'))
		flash("Invalid email.", 'warning')
		return redirect(url_for('.forget_password'))
	return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	
	form = ResetPasswordForm()
	if form.validate_on_submit():
		email = form.email.data.lower()
		user = User.query.filter_by(email=email).first()
		if not user:
			return redirect(url_for('main.index'))
		new_password = form.password.data
		if validate_token(user, token, Operations.RESET_PASSWORD, new_password=new_password):
			flash('Password updated', 'success')
			return redirect(url_for('.login'))
		else:
			flash('Invalid or expired link.', 'danger')
			return redirect(url_for('.forget_password'))
	# 问题：如何针对未登录用户进行验证？要怎么修改？user参数怎么传？
	# 在post时候再验证
	return render_template('auth/reset_password.html', form=form)

	