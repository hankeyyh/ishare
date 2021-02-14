# coding: utf-8

from flask import url_for
from albumy.models import Notification
from albumy.extensions import db


def push_follow_notification(follower, receiver):
	"""当被人关注时推送"""
	message = 'User <a href="%s">%s</a> followed you.' % \
	          (url_for('user.index', username=follower.username), follower.username)
	notification = Notification(message=message, receiver=receiver)
	db.session.add(notification)
	db.session.commit()


def push_comment_notification(photo_id, receiver, page=1):
	"""照片被人评论时推送"""
	message = "<a href='%s#comments'>This photo </a> has new comment/reply." % \
	          url_for('main.show_photo', photo_id=photo_id, page=page)
	notification = Notification(message=message, receiver=receiver)
	db.session.add(notification)
	db.session.commit()


def push_collect_notification(collector, photo_id, receiver):
	"""照片被收藏时推送"""
	message = 'User <a href="%s">%s</a> collected your <a href="%s">photo</a>' % \
	          (url_for('user.index', username=collector.username),
	           collector.username,
	           url_for('main.show_photo', photo_id=photo_id))
	notification = Notification(message=message, receiver=receiver)
	db.session.add(notification)
	db.session.commit()