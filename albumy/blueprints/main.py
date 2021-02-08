# coding: utf-8
import os

from flask import Blueprint, render_template, request, current_app, send_from_directory, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from albumy import db
from albumy.decorators import confirm_required, permission_required
from albumy.models import Photo
from albumy.utils import rename_image, resize_image

main_bp = Blueprint("main", __name__)

@main_bp.route('/')
def index():
	return render_template('main/index.html')

@main_bp.route('/explore')
def explore():
	return render_template('main/explore.html')

@main_bp.before_request
@login_required
def login_protected():
	pass


@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@confirm_required
@permission_required('UPLOAD')
def upload():
	"""
	获取file，重命名，保存，创建Photo对象
	"""
	if request.method == 'POST' and 'file' in request.files:
		f = request.files.get('file')
		filename = rename_image(f.filename)
		f.save(os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename))
		filename_s = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['small'])
		filename_m = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['medium'])
		photo = Photo(
			filename=filename,
			filename_s=filename_s,
			filename_m=filename_m,
			author=current_user._get_current_object()
		)
		db.session.add(photo)
		db.session.commit()
	return render_template('main/upload.html')


@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
	return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)

@main_bp.route('/uploads/<path:filename>')
def get_image(filename):
	return send_from_directory(current_app.config['ALBUMY_UPLOAD_PATH'], filename)

@main_bp.route('/photo/<int:photo_id>')
def show_photo(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	return render_template('main/photo.html', photo=photo)

@main_bp.route('/report_photo/<photo_id>')
def report_photo(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	return redirect(url_for('.show_photo', photo_id=photo_id))

@main_bp.route('/delete_photo/<photo_id>', methods=['POST'])
def delete_photo(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	if current_user != photo.author:
		abort(403)
	db.session.delete(photo)
	db.session.commit()
	flash('Photo deleted.', 'info')
	
	photo_n = Photo.query.with_parent(current_user).filter(Photo.id < photo_id).order_by(Photo.id.desc()).first()
	if photo_n:
		return redirect(url_for('.show_photo', photo_id=photo_n.id))

	photo_p = Photo.query.with_parent(current_user).filter(Photo.id < photo_id).order_by(Photo.id.desc()).first()
	if photo_p:
		return redirect(url_for('.show_photo', photo_id=photo_p.id))
	return redirect(url_for('user.index', username=current_user.username))

@main_bp.route('/photo/n/<int:photo_id>')
def photo_next(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	photo_n = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).order_by(Photo.id.desc()).first()
	if not photo_n:
		flash("This is the last photo.", "info")
		return redirect(url_for('.show_photo', photo_id=photo_id))
	return redirect(url_for('.show_photo', photo_id=photo_n.id))

@main_bp.route('/photo/p/<int:photo_id>')
def photo_previous(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	photo_p = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.id.asc()).first()
	if photo_p is None:
		flash('This is already the first one.', 'info')
		return redirect(url_for('.show_photo', photo_id=photo_id))
	return redirect(url_for('.show_photo', photo_id=photo_p.id))