# coding: utf-8
import os
import sys

platform = sys.platform
if 'win' in platform.lower():
	prefix = 'sqlite:///'
else:
	prefix = 'sqlite:////'

base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class BaseConfig(object):
	SECRET_KEY = os.getenv('SECRET_KEY', 'secret key')
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	# mail
	MAIL_SERVER = os.getenv("MAIL_SERVER", 'localhost')
	MAIL_PORT = 587
	MAIL_USE_TLS = True
	MAIL_USERNAME = os.getenv('MAIL_USERNAME')
	MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
	MAIL_DEFAULT_SENDER = ('iShare', os.getenv('MAIL_USERNAME'))
	ALBUMY_MAIL_SUBJECT_PREFIX = '[iShare]'
	# role
	ALBUMY_ADMIN_EMAIL = os.getenv('ALBUMY_ADMIN', 'hankeyyh@outlook.com')
	# photo
	ALBUMY_UPLOAD_PATH = os.path.join(base_dir, 'uploads')
	ALBUMY_PHOTO_SIZE = {'small': 400, 'medium': 800}
	ALBUMY_PHOTO_SUFFIX = {
		ALBUMY_PHOTO_SIZE['small']: '_s',  # thumbnail
		ALBUMY_PHOTO_SIZE['medium']: '_m',  # display
	}
	ALBUMY_PHOTO_PER_PAGE = 12
	# dropzone
	DROPZONE_ALLOWED_FILE_TYPE = 'image'
	DROPZONE_MAX_FILE_SIZE = 3
	DROPZONE_MAX_FILES = 30
	DROPZONE_ENABLE_CSRF = True
	# avatar
	AVATARS_SAVE_PATH = os.path.join(ALBUMY_UPLOAD_PATH, 'avatars')
	AVATARS_SIZE_TUPLE = (30, 100, 200)
	# comment
	ALBUMY_COMMENT_PER_PAGE = 15
	ALBUMY_MANAGE_COMMENT_PER_PAGE = 30
	# collector
	ALBUMY_USER_PER_PAGE = 20
	
	
class DevConfig(BaseConfig):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = prefix + os.path.join(base_dir, 'dev.db')

class PubConfig(BaseConfig):
	SQLALCHEMY_DATABASE_URI = prefix + os.path.join(base_dir, 'pub.db')
	
	
configs = {
	'dev': DevConfig,
	'pub': PubConfig
}

class Operations:
	CONFIRM = 'confirm'
	RESET_PASSWORD = 'reset-password'
	CHANGE_EMAIL = 'change-email'