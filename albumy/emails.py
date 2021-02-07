# coding: utf-8
from threading import Thread

from flask_mail import Message
from albumy import mail
from flask import current_app, render_template


def _send_mail_async(app, message):
	with app.app_context():
		mail.send(message)


def send_mail(subject, to, template, **kwargs):
	message = Message(current_app.config['ALBUMY_MAIL_SUBJECT_PREFIX'] + subject, recipients=[to])
	message.body = render_template(template + '.txt', **kwargs)
	message.html = render_template(template + '.html', **kwargs)
	app = current_app._get_current_object()
	thr = Thread(target=_send_mail_async, args=[app, message])
	thr.start()
	return thr


def send_confirm_email(user, token, to=None):
	send_mail(subject='Email Confirm', to=to or user.email, template='emails/confirm', user=user, token=token)
	
def send_reset_password_email(user, token):
	send_mail(subject='Reset Password', to=user.email, template='emails/reset_password', user=user, token=token)