# coding: utf-8
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask_mail import Mail
from flask_login import LoginManager, AnonymousUserMixin
from flask_dropzone import Dropzone
from flask_wtf import CSRFProtect
from flask_avatars import Avatars

db = SQLAlchemy()
bootstrap = Bootstrap()
moment = Moment()
mail = Mail()
login_manager = LoginManager()
dropzone = Dropzone()
csrf = CSRFProtect()
avatars = Avatars()

@login_manager.user_loader
def load_user(user_id):
    from albumy.models import User
    print('user.id: ', user_id)
    user = User.query.get(int(user_id))
    print('user: ', user)
    return user


class Guest(AnonymousUserMixin):
    """游客"""
    
    def can(self, permission_name):
        """验证权限"""
        return False
    
    @property
    def is_admin(self):
        return False
    
login_manager.login_view = 'auth.login'
login_manager.login_message = ''
login_manager.login_message_category = 'warning'
login_manager.anonymous_user = Guest