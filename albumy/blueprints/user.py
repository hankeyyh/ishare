# coding: utf-8
from flask import Blueprint, render_template, request, current_app
from flask_login import current_user

from albumy.models import User, Photo, Collect

user_bp = Blueprint('user', __name__)

@user_bp.route('/<username>')
def index(username):
	"""
	获取当前页码，db.photo按照时间顺序分页
	"""
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1, type=int)
	per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
	pagination = Photo.query.with_parent(user).order_by(Photo.timestamp.desc()).paginate(page, per_page)
	photos = pagination.items
	return render_template('user/index.html', user=user, pagination=pagination, photos=photos)


@user_bp.route('/<username>/collections')
def show_collections(username):
	"""显示收藏的照片"""
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1)
	per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
	pagination = Collect.query.with_parent(user).order_by(Collect.timestamp.desc()).paginate(page, per_page)
	collects = pagination.items
	return render_template('user/collections.html', user=user, pagination=pagination, collects=collects)