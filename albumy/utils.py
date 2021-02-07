# coding: utf-8
import os
import uuid
from threading import Thread

import PIL
from PIL import Image

from albumy.settings import Operations

try:
	from urlparse import urlparse, urljoin
except ImportError:
	from urllib.parse import urlparse, urljoin
 
from flask import request, url_for, redirect, flash, current_app
from flask_mail import Message
from albumy import mail, db
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature


def is_safe_url(target):
	ref_url = urlparse(request.host_url)
	test_url = urlparse(urljoin(request.host_url, target))
	# 什么情况下，netloc会被改掉？
	return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def redirect_back(default='main.index', **kwargs):
	for target in request.args.get('next'), request.referrer:
		if not target:
			continue
		if is_safe_url(target):
			print('target: ', target)
			return redirect(target)
	return redirect(url_for(default, **kwargs))

def flash_error(form):
	for field, errors in form.errors.items():
		for error in errors:
			flash(u"Error in the %s field - %s" % (form.field.label.text, error))


def generate_token(user, operation, expires_in=None, **kwargs):
	s = Serializer(current_app.config['SECRET_KEY'], expires_in)
	data = {'id': user.id, 'operation': operation}
	data.update(**kwargs)
	return s.dumps(data)


def validate_token(user, token, operation, new_password=None):
	s = Serializer(current_app.config['SECRET_KEY'])
	try:
		data = s.loads(token)
	except (SignatureExpired, BadSignature):
		return False
	
	if operation != data.get('operation') or user.id != data.get('id'):
		return False
	
	if operation == Operations.CONFIRM:
		user.confirmed = True
	elif operation == Operations.RESET_PASSWORD:
		user.set_password(new_password)
	else:
		return False
	
	db.session.commit()
	return True

def rename_image(old_filename):
	ext = os.path.splitext(old_filename)[1]
	new_filename = uuid.uuid4().hex + ext
	return new_filename


def resize_image(image, filename, base_width):
	"""
	提取filename，ext；计算w_percent，计算新高度；执行缩放；重命名filename；保存
	"""
	filename, ext = os.path.splitext(filename)
	img = Image.open(image)
	if img.size[0] <= base_width:
		return filename + ext
	w_percent = (base_width / float(img.size[0]))
	h_size = int((float(img.size[1]) * float(w_percent)))
	img = img.resize((base_width, h_size), PIL.Image.ANTIALIAS)
	
	filename += current_app.config['ALBUMY_PHOTO_SUFFIX'][base_width] + ext
	img.save(os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename), optimize=True, quality=85)
	return filename