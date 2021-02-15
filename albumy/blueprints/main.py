# coding: utf-8
import os

from flask import Blueprint, render_template, request, current_app, send_from_directory, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from albumy.utils import flash_errors
from albumy import db
from albumy.decorators import confirm_required, permission_required
from albumy.models import Photo, Tag, Comment, Collect, Notification, Follow
from albumy.utils import rename_image, resize_image
from albumy.forms.main import DescriptionForm, TagForm, CommentForm
from albumy.notifications import push_comment_notification, push_collect_notification
from sqlalchemy.sql.expression import func

main_bp = Blueprint("main", __name__)

@main_bp.route('/')
def index():
	if current_user.is_authenticated:
		page = request.args.get('page', 1, type=int)
		per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
		pagination = Photo.query \
			.join(Follow, Follow.followed_id == Photo.author_id) \
			.filter(Follow.follower_id == current_user.id) \
			.order_by(Photo.timestamp.desc()) \
			.paginate(page, per_page)
		photos = pagination.items
	else:
		pagination = None
		photos = None
	return render_template('main/index.html', pagination=pagination, photos=photos)

@main_bp.route('/explore')
def explore():
	photos = Photo.query.order_by(func.random()).limit(12)
	return render_template('main/explore.html', photos=photos)

@main_bp.before_request
@login_required
def login_protected():
	pass


@main_bp.route('/upload', methods=['GET', 'POST'])
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
	description_form = DescriptionForm()
	description_form.description.data = photo.description
	tag_form = TagForm()

	comment_form = CommentForm()
	page = request.args.get('page', 1, type=int)
	per_page = current_app.config['ALBUMY_COMMENT_PER_PAGE']
	pagination = Comment.query.with_parent(photo).order_by(Comment.timestamp.asc()).paginate(page, per_page)
	comments = pagination.items
	return render_template('main/photo.html', photo=photo, comment_form=comment_form,
	                       description_form=description_form, tag_form=tag_form,
	                       pagination=pagination, comments=comments)

@main_bp.route('/tag/<int:tag_id>', defaults={'order': 'by_time'})
@main_bp.route("/tag/<int:tag_id>/<order>")
def show_tag(tag_id, order):
	tag = Tag.query.get_or_404(tag_id)
	page = request.args.get('page', 1, type=int)
	per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
	pagination = Photo.query.with_parent(tag).order_by(Photo.timestamp.desc()).paginate(page, per_page)
	photos = pagination.items
	order_rule = 'time'
	if order == 'by_collects':
		photos.sort(key=lambda x: len(x.collectors), reverse=True)
		order_rule = 'collects'

	return render_template('main/tag.html', tag=tag, pagination=pagination, photos=photos, order_rule=order_rule)


@main_bp.route('/photo/<int:photo_id>/tag/new', methods=['POST'])
def new_tag(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	if current_user != photo.author:
		abort(403)
	tag_form = TagForm()
	if tag_form.validate_on_submit():
		tag_names = tag_form.tag.data.split()
		for tag_name in tag_names:
			tag = Tag.query.filter_by(name=tag_name).first()
			if not tag:
				tag = Tag(name=tag_name)
				db.session.add(tag)
				# db.session.commit()
			if tag not in photo.tags:
				photo.tags.append(tag)
			db.session.commit()
		flash("Tag added.", 'success')

	flash_errors(tag_form)
	return redirect(url_for('.show_photo', photo_id=photo_id))

@main_bp.route('/delete/tag/<int:photo_id>/<int:tag_id>', methods=['POST'])
def delete_tag(photo_id, tag_id):
	photo = Photo.query.get_or_404(photo_id)
	if current_user != photo.author:
		abort(403)
	tag = Tag.query.get_or_404(tag_id)
	photo.tags.remove(tag)
	db.session.commit()

	if not tag.photos:
		db.session.delete(tag)
		db.session.commit()

	flash('Tag deleted.', 'info')
	return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/report_photo/<photo_id>', methods=['POST'])
@confirm_required
def report_photo(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	photo.flag += 1
	db.session.commit()
	flash('Photo reported.', 'success')
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

@main_bp.route('/photo/<int:photo_id>/description', methods=['POST'])
def edit_description(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	if current_user != photo.author:
		abort(403)

	form = DescriptionForm()
	if form.validate_on_submit():
		photo.description = form.description.data
		db.session.commit()
		flash('Description updated.', 'success')

	flash_errors(form)
	return redirect(url_for('.show_photo', photo_id=photo_id))

@main_bp.route('/report/comment/<int:comment_id>', methods=['POST'])
@confirm_required
def report_comment(comment_id):
	comment = Comment.query.get_or_404(comment_id)
	comment.flag += 1
	db.session.commit()
	flash('Comment reported.', 'success')
	return redirect(url_for('.show_photo', photo_id=comment.photo_id))

@main_bp.route('/photo/<int:photo_id>/comment/new', methods=['POST'])
@permission_required("COMMENT")
def new_comment(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	comment_form = CommentForm()
	page = request.args.get('page', 1, type=int)
	if comment_form.validate_on_submit():
		comment = Comment(body=comment_form.body.data,
		                  photo=photo,
		                  author=photo.author)

		replied_id = request.args.get('reply')
		if replied_id:
			comment.replied = Comment.query.get_or_404(replied_id)
			push_comment_notification(photo_id, comment.replied.author)
		db.session.add(comment)
		db.session.commit()
		flash('Comment published.', 'success')

		if current_user != photo.author:
			push_comment_notification(photo_id, photo.author, page)

	flash_errors(comment_form)
	return redirect(url_for('.show_photo', photo_id=photo_id, page=page))


@main_bp.route('/set-comment/<int:photo_id>')
def set_comment(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	if current_user != photo.author:
		abort(403)
	if photo.can_comment:
		photo.can_comment = False
		flash('Comment disabled', 'info')
	else:
		photo.can_comment = True
		flash('Comment enabled.', 'info')
	db.session.commit()
	return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/delete-comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
	comment = Comment.query.get_or_404(comment_id)
	if current_user != comment.author and current_user != comment.photo.author:
		abort(403)
	db.session.delete(comment)
	db.session.commit()
	flash('Comment deleted.', 'info')
	return redirect(url_for('.show_photo', photo_id=comment.photo_id))

@main_bp.route('/reply/comment/<int:comment_id>')
def reply_comment(comment_id):
	comment = Comment.query.get_or_404(comment_id)
	return redirect(url_for('.show_photo', photo_id=comment.photo_id,
	                        reply=comment_id, author=comment.author.name) + '#comment-form')


@main_bp.route('/collect/<int:photo_id>', methods=['POST'])
@confirm_required
@permission_required("COLLECT")
def collect(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	if current_user.is_collecting(photo):
		flash('Already collected.', 'info')
		return render_template(url_for('.show_photo', photo_id=photo_id))

	current_user.collect(photo)
	flash('Photo collected.', 'success')
	if current_user != photo.author:
		push_collect_notification(current_user, photo_id, photo.author)

	return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/uncollect/<int:photo_id>', methods=['POST'])
def uncollect(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	if not current_user.is_collecting(photo):
		flash('No collected yet.', 'info')
		return render_template(url_for('.show_photo', photo_id=photo_id))

	current_user.uncollect(photo)
	flash('Photo uncollected.', 'success')
	return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/collectors/<int:photo_id>')
def show_collectors(photo_id):
	photo = Photo.query.get_or_404(photo_id)
	page = request.args.get('page', 1)
	per_page = current_app.config['ALBUMY_USER_PER_PAGE']
	pagination = Collect.query.with_parent(photo).order_by(Collect.timestamp.asc()).paginate(page, per_page)
	collects = pagination.items
	return render_template('main/collectors.html', collects=collects, photo=photo, pagination=pagination)


@main_bp.route('/notifications')
def show_notifications():
	page = request.args.get('page', 1)
	per_page = current_app.config['ALBUMY_NOTIFICATION_PER_PAGE']
	notifications = Notification.query.with_parent(current_user)
	filter_rule = request.args.get('filter')
	if filter_rule == 'unread':
		notifications = notifications.filter_by(is_read=False)
	pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
	notifications = pagination.items
	return render_template('main/notifications.html', pagination=pagination, notifications=notifications)


@main_bp.route('/notification/read/<int:notification_id>', methods=['POST'])
def read_notification(notification_id):
	notification = Notification.query.get_or_404(notification_id)
	if current_user != notification.receiver:
		abort(403)
	notification.is_read = True
	db.session.commit()
	flash('Notification archived.', 'success')
	return redirect(url_for('.show_notifications'))


@main_bp.route('/notifications/read/all', methods=['POST'])
def read_all_notification():
	for notification in current_user.notifications:
		notification.is_read = True
	db.session.commit()
	flash('All notifications archived.', 'success')
	return redirect(url_for('.show_notifications'))