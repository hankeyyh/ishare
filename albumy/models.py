# coding: utf-8
import os

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from albumy.extensions import db
from flask_login import UserMixin
from flask_avatars import Identicon


role_permissions = db.Table('role_permissions',
                            db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                            db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
                            )

tagging = db.Table('tagging',
                   db.Column('photo_id', db.Integer, db.ForeignKey('photo.id')),
                   db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                   )


class Collect(db.Model):
	"""连接user，photo多对多关系"""
	collector_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	collected_id = db.Column(db.Integer, db.ForeignKey('photo.id'), primary_key=True)
	collector = db.relationship('User', back_populates='collections', lazy='joined')
	collected = db.relationship('Photo', back_populates='collectors', lazy='joined')
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Follow(db.Model):
	"""连接user, user多对多关系"""
	follower_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)  # 关注者
	followed_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)  # 被关注者
	follower = db.relationship('User', foreign_keys=[follower_id], back_populates='following', lazy='joined')
	followed = db.relationship('User', foreign_keys=[followed_id], back_populates='followers', lazy='joined')
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model, UserMixin):
	"""用户"""
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, index=True)
	email = db.Column(db.String(254), unique=True, index=True)
	password_hash = db.Column(db.String(128))
	name = db.Column(db.String(30))
	website = db.Column(db.String(255))
	bio = db.Column(db.String(120))
	location = db.Column(db.String(50))
	member_since = db.Column(db.DateTime, default=datetime.utcnow)
	avatar_s = db.Column(db.String(64))
	avatar_m = db.Column(db.String(64))
	avatar_l = db.Column(db.String(64))
	confirmed = db.Column(db.Boolean, default=False)

	# role
	role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
	role = db.relationship('Role', back_populates='users')
	# own photos
	photos = db.relationship('Photo', back_populates='author', cascade='all')
	# comments
	comments = db.relationship('Comment', back_populates='author', cascade='all')
	# collect photos
	collections = db.relationship('Collect', back_populates='collector', cascade='all')
	# follow
	following = db.relationship("Follow", foreign_keys=[Follow.follower_id], back_populates='follower',
	                            lazy='dynamic', cascade='all')
	followers = db.relationship("Follow", foreign_keys=[Follow.followed_id], back_populates='followed',
	                            lazy='dynamic', cascade='all')
	# notification
	notifications = db.relationship('Notification', back_populates='receiver', cascade='all')

	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
		self.set_role()
		self.generate_avatars()
		self.follow(self)
		
	def generate_avatars(self):
		avatar = Identicon()
		filenames = avatar.generate(text=self.username)
		self.avatar_s, self.avatar_m, self.avatar_l = filenames
		db.session.commit()
		
	def set_role(self):
		"""设置角色"""
		if self.role: return
		
		if self.email == current_app.config['ALBUMY_ADMIN_EMAIL']:
			self.role = Role.query.filter_by(name='Administrator').first()
		else:
			self.role = Role.query.filter_by(name='User').first()
		db.session.commit()
		
	def can(self, permission_name):
		"""验证权限"""
		permission = Permission.query.filter_by(name=permission_name).first()
		return permission is not None and self.role is not None and permission in self.role.permissions
	
	@property
	def is_admin(self):
		return self.role.name == 'Administrator'
	
	def set_password(self, password):
		self.password_hash = generate_password_hash(password)
	
	def validate_password(self, password):
		return check_password_hash(self.password_hash, password)

	@property
	def followed_photos(self):
		return Photo.query.join(Follow, Follow.followed_id == Photo.author_id).filter(Follow.follower_id == self.id)

	def collect(self, photo):
		"""收藏图片"""
		if self.is_collecting(photo):
			return
		collect = Collect(collector=self, collected=photo)
		db.session.add(collect)
		db.session.commit()

	def uncollect(self, photo):
		"""取消收藏"""
		collect = Collect.query.with_parent(self).filter_by(collected_id=photo.id).first()
		if collect:
			db.session.delete(collect)
			db.session.commit()

	def is_collecting(self, photo):
		"""图片是否已收藏"""
		return Collect.query.with_parent(self).filter_by(collected_id=photo.id).first() is not None

	def follow(self, user):
		if self.is_following(user):
			return
		follow = Follow(follower=self, followed=user)
		db.session.add(follow)
		db.session.commit()

	def unfollow(self, user):
		follow = self.following.filter_by(followed_id=user.id).first()
		if follow:
			db.session.delete(follow)
			db.session.commit()

	def is_following(self, user):
		# 创建用户后用户首先会关注自身,因为还没有提交数据库会话, user.id will be None
		if user.id is None:
			return False
		return self.following.filter_by(followed_id=user.id).first() is not None

	def is_followed_by(self, user):
		return self.followers.filter_by(follower_id=user.id).first() is not None


class Photo(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	description = db.Column(db.String(500))
	filename = db.Column(db.String(64))
	filename_s = db.Column(db.String(64))
	filename_m = db.Column(db.String(64))
	timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
	can_comment = db.Column(db.Boolean, default=True)
	flag = db.Column(db.Integer, default=0)
	# author
	author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	author = db.relationship('User', back_populates='photos')
	# tag
	tags = db.relationship("Tag", secondary=tagging, back_populates='photos')
	# comments
	comments = db.relationship('Comment', back_populates='photo', cascade='all')
	# collector
	collectors = db.relationship('Collect', back_populates='collected', cascade='all')


@db.event.listens_for(Photo, 'after_delete', named=True)
def delete_photo(**kwargs):
	target = kwargs['target']
	for filename in (target.filename, target.filename_s, target.filename_m):
		path = os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename)
		if os.path.exists(path):
			os.remove(path)


class Permission(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), unique=True)
	roles = db.relationship('Role', secondary=role_permissions, back_populates='permissions')
	

class Role(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), unique=True)
	users = db.relationship('User', back_populates='role')
	permissions = db.relationship('Permission', secondary=role_permissions, back_populates='roles')
	
	@staticmethod
	def init_role():
		roles_permissions_map = {
			'Locked': ['FOLLOW', 'COLLECT'],
			'User': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD'],
			'Moderator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE'],
			'Administrator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE', 'ADMINISTER']
		}
		for role_name, permissions in roles_permissions_map.items():
			role = Role.query.filter_by(name=role_name).first()
			if not role:
				role = Role(name=role_name)
				db.session.add(role)
				
			role.permissions = []
			for pname in permissions:
				permission = Permission.query.filter_by(name=pname).first()
				if not permission:
					permission = Permission(name=pname)
					db.session.add(permission)
				role.permissions.append(permission)
				
		db.session.commit()


class Tag(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), index=True, unique=True)

	photos = db.relationship("Photo", secondary=tagging, back_populates='tags')


class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
	flag = db.Column(db.Integer, default=0)

	replied_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
	author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'))

	photo = db.relationship('Photo', back_populates='comments')
	author = db.relationship('User', back_populates='comments')
	replies = db.relationship('Comment', back_populates='replied', cascade='all')
	replied = db.relationship('Comment', back_populates='replies', remote_side=[id])


class Notification(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	message = db.Column(db.Text)
	is_read = db.Column(db.Boolean, default=False)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
	receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	receiver = db.relationship('User', back_populates='notifications')