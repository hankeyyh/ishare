# coding: utf-8
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from albumy.extensions import db
from flask_login import UserMixin
from flask_avatars import Identicon


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

	confirmed = db.Column(db.Boolean, default=False)
	
	role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
	role = db.relationship('Role', back_populates='users')
	
	photos = db.relationship('Photo', back_populates='author', cascade='all')
	
	# avatar
	avatar_s = db.Column(db.String(64))
	avatar_m = db.Column(db.String(64))
	avatar_l = db.Column(db.String(64))
	
	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
		self.set_role()
		self.generate_avatars()
		
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
	
	
	
role_permissions = db.Table('role_permissions',
                            db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                            db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
                            )

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
	
	
	
class Photo(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	description = db.Column(db.String(30))
	filename = db.Column(db.String(64))
	filename_s = db.Column(db.String(64))
	filename_m = db.Column(db.String(64))
	timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
	author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	author = db.relationship('User', back_populates='photos')
	

