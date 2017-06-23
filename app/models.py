# -*- coding: utf-8 -*-
from . import db, login_manager
from flask import current_app, request
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
import hashlib


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    # users 属性代表了这个关系的面向对象视角。对于一个 Role 类的实例，其 users 属性将返回
    # 与角色相关联的用户组成的列表。第一个参数表明这个关系的另一端是哪个模型。
    # backref 参数向 User 模型中添加一个 role 属性，从而定义反向关系。
    # 这一属性可替代 role_id 访问 Role 模型，此时获取的是模型对象，而不是外键的值
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': True,
            'Administrator': False
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.default = roles[r]
            db.session.add(role)
        db.session.commit()


# 要想使用 Flask-Login 扩展，管理用户认证系统的认证状态，
# 程序的 User 模型必须实现以下几个方法：
#   is_authenticated    如果用户已经登录，必须返回 True,否则返回 False
#   is_active   如果允许用户登录，必须返回 True,否则返回 False。如果要禁用账户，可以返回 False
#   is_anonymous    对于普通用户必须返回 False
#   get_id()    必须返回用户的唯一标识符，使用 Unicode 编码字符串
# 这4个方法可以在 User 模型类中作为方法直接实现，不过 Flask-Login 提供了一个 UserMixin 类，
# 包含了这些方法的默认实现，且能满足大多数需求
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    # role_id 这个外键建立起了 User 模型和 Role 模型的联系
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    # 要保证数据库中用户密码的安全，不存储密码本身，而是存储密码的散列值
    # Werkzeug 中的 security 模块能够很方便地实现密码散列值的计算和验证。
    # 注册用户时，generate_password_hash(password) 将原始密码作为输入，以字符串形式输出密码的散列值
    # 验证用户时，check_password_hash(hash, password) hash是从数据库中取回的密码散列值，password 是用户输入的密码，
    # 对两者进行比对，密码正确返回 True，密码错误返回 False
    password_hash = db.Column(db.String(128))
    # 因为要通过发送验证电子邮件的方式确认注册的新用户，所以一开始新用户被标记为待确认状态
    confirmed = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow())
    last_logout = db.Column(db.DateTime, default=datetime.utcnow())
    avatar_hash = db.Column(db.String(32))

    # tasks 属性代表了这个关系的面向对象视角。对于一个 User 类的实例，其 tasks 属性将返回
    # 与角色相关联的任务组成的列表。第一个参数表明这个关系的另一端是哪个模型。
    # backref 参数向 Task 模型中添加一个 user_task 属性，从而定义反向关系。
    # 这一属性可替代 user_id 访问 Task 模型，此时获取的是模型对象，而不是外键的值
    tasks = db.relationship('Task', backref='user_task', lazy='dynamic')

    # tasks 属性代表了这个关系的面向对象视角。对于一个 User 类的实例，其 taskTemps 属性将返回
    # 与角色相关联的任务组成的列表。第一个参数表明这个关系的另一端是哪个模型。
    # backref 参数向 Task 模型中添加一个 user_taskTemp 属性，从而定义反向关系。
    # 这一属性可替代 user_id 访问 TaskTemp 模型，此时获取的是模型对象，而不是外键的值
    taskTemps = db.relationship('TaskTemp', backref='user_taskTemp', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(default=False).first()
            else:
                self.role = Role.query.filter_by(default=True).first()
            if self.email is not None and self.avatar_hash is None:
                self.avatar_hash = hashlib.md5(
                    self.email.encode('utf-8')).hexdigest()

    # @property 修饰器对 password 方法进行修饰，从而使其可以像类似 User 模型属性的方式直接访问
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    # setter方法保证设置 password 时，调用 Werkzeug 提供的 generate_password_hash() 函数生成 password_hash
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 使用 itsdangerous 生成确认邮件链接中用户 id 的确认令牌
    # 确认邮件中最简单的确认链接是 http://www.example.com/auth/confirm/<id>这种形式的 URL，其中 id 是数据库
    # 分配给用户的数字 id 。用户点击链接后，处理这个路由的视图函数就将收到的用户 id 作为参数进行确认，然后将用户状态更新为已确认
    # 但是这种方式显然不安全，只要用户能判断确认链接的格式，就可以随便指定 URL 中的 id ，从而确认任意账户。解决办法是把 URL 中的
    # id 换成加密后得到的令牌。使用 itsdangerous 包的 TimedJSONWebSignatureSerializer 类可以生成具有过期时间的 JSON Web 签名
    # (JSON Web Signatures, JWS)。这个类的构造函数接收的参数是一个秘钥，在 Flask 程序中可使用 SECRET_KEY 设置
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            # 解码令牌使用序列化对象的 loads() 方法，其唯一的参数是令牌字符串。这个方法会检验签名和过期时间，如果通过，返回原始数据。
            # 如果提供给 loads() 方法的令牌不正确或已过期，则抛出异常
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        # 验证通过把用户确认状态更新为已确认
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset_password': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset_password') != self.id:
            return False
        # 验证通过，调用经 @property 修饰器修饰后的 password 方法(属性)重置密码
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        # 将用户输入的新的电子邮件地址和用户 id 一起保存在更改邮箱的令牌中
        return s.dumps({'change_email':self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def is_Administrator(self):
        return self.role.name == "Administrator"

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        # Gravatar 查询字符串参数，可以配置头像图片的特征
        #   s:  图片大小，单位为像素
        #   r:  图片级别。可选值有 "g"(普通级)、 "pg"(辅导级)、"r"和"x"(限制级)
        #   d:  没有注册 Gravatar 服务的用户使用的默认图片的生成方式
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    # 在用户登录时调用 last_login_time() 更新用户的登录时间
    def last_login_time(self):
        self.last_login = datetime.utcnow()
        db.session.add(self)

    # 在用户登出时调用 last_logout_time() 更新用户的登出时间
    def last_logout_time(self):
        self.last_logout = datetime.utcnow()
        db.session.add(self)


class DSP_Status(object):
    IDLE = 0x00
    RUNNING = 0x01


class CalBoard(db.Model):
    __tablename__ = 'calBoard'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    existing = db.Column(db.Boolean, default=True)
    dsp1_status = db.Column(db.SmallInteger)
    dsp2_status = db.Column(db.SmallInteger)
    fpga_extra = db.Column(db.Integer)

    @staticmethod
    def insert_calBoards():
        calBoards = {
            'cb1': (DSP_Status.IDLE, DSP_Status.IDLE, 0),
            'cb2': (DSP_Status.IDLE, DSP_Status.IDLE, 0),
            'cb3': (DSP_Status.IDLE, DSP_Status.IDLE, 0),
            'cb4': (DSP_Status.IDLE, DSP_Status.IDLE, 0),
            'cb5': (DSP_Status.IDLE, DSP_Status.IDLE, 0),
            'cb6': (DSP_Status.IDLE, DSP_Status.IDLE, 0),
            'cb7': (DSP_Status.IDLE, DSP_Status.IDLE, 0),
            'cb8': (DSP_Status.IDLE, DSP_Status.IDLE, 0),
        }
        for cb in calBoards:
            calBoard = CalBoard.query.filter_by(name=cb).first()
            if calBoard is None:
                calBoard = CalBoard(name=cb)
            calBoard.dsp1_status, calBoard.dsp2_status,\
                calBoard.fpga_extra = calBoards[cb]
            db.session.add(calBoard)
        db.session.commit()

    def dsp1_isIdle(self):
        return self.dsp1_status == DSP_Status.IDLE

    def dsp2_isIdle(self):
        return self.dsp2_status == DSP_Status.IDLE

    def set_exiting(self):
        self.existing = True

    def set_noExiting(self):
        self.existing = False


class StoreBoard(db.Model):
    __tablename__ = 'storeBoard'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    capacity = db.Column(db.Integer)
    used = db.Column(db.Integer)
    left = db.Column(db.Integer)

    @staticmethod
    def insert_storeBoards():
        storeBoards = {
            'sb1': (2048, 0),
            'sb2': (2048, 1024),
            'sb3': (2048, 1536),
            'sb4': (2048, 512),
        }
        for sb in storeBoards:
            storeBoard = StoreBoard.query.filter_by(name=sb).first()
            if storeBoard is None:
                storeBoard = StoreBoard(name=sb)
            storeBoard.capacity, storeBoard.used = storeBoards[sb]
            storeBoard.left = storeBoard.capacity - storeBoard.used
            db.session.add(storeBoard)
        db.session.commit()


class ControlBoard(db.Model):
    __tablename__ = 'controlBoard'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    cpu_sys_percent = db.Column(db.Float)
    cpu_user_percent = db.Column(db.Float)
    cpu_idle_percent = db.Column(db.Float)

    @staticmethod
    def genControlData():
        import psutil
        import re
        import time
        # 利用 psutil 模块获得有 interval=1 指定的接下来1s内
        # cpu 的详细使用率
        cpu_percents = str(psutil.cpu_times_percent(interval=1))

        #    print(cpu_percents)

        # 使用正则匹配出 user system 以及 idle 对应的 cpu 占用率
        m = re.match(r'.*(user=\d+\.?\d+).*(system=\d+\.?\d+).*(idle=\d+\.?\d+).*',
                     cpu_percents)

        # 利用一个字典保存 user system idle 对应的 cpu 占用率
        dict = {}
        for d in m.groups():
            (k, v) = d.split('=')
            dict[k] = float(v)

        # 存入当前的系统时间戳
        # dict['time'] = time.mktime(datetime.utcnow().timetuple())
        # 存入当前的 UTC 时间
        dict['time'] = datetime.utcnow()

        return dict

    @staticmethod
    def insert_controlBoards(count=20):
        for i in range(count):
            dict = ControlBoard.genControlData()
            crtlb = ControlBoard(cpu_user_percent=dict['user'],
                         cpu_sys_percent=dict['system'],
                         cpu_idle_percent=dict['idle'],
                         timestamp=dict['time'])
            db.session.add(crtlb)
            try:
                db.session.commit()
            except Exception as err:
                print('Add data to ControlBoard model occurs error: %s' % err)
                db.session.rollback()

class Task_Status(object):
    WAITING = 0x00          # 等待
    EXECUTABLE = 0x01       # 可执行
    RUNNING = 0x02          # 执行中
    DONE = 0x03             # 执行完毕


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)
    attr = db.Column(db.String)
    data_file_name = db.Column(db.String)
    data_treated_file_name = db.Column(db.String)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    # 任务状态
    task_status = db.Column(db.SmallInteger, default=Task_Status.WAITING)
    # 任务 id ，由主控板生成并返回
    task_id = db.Column(db.SmallInteger, default=-1)
    task_hwResource = db.Column(db.String, default='')
    # user_id 这个外键建立起 Task 模型与 User 模型之间多对一的关系
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class TaskTemp(db.Model):
    __tablename__ = 'taskTemps'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)
    attr = db.Column(db.String)
    data_file_name = db.Column(db.String)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    # user_id 这个外键建立起 Task 模型与 User 模型之间多对一的关系
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# 最后，Flask-Login 要求程序实现一个回调函数，使用指定的标识符加载用户
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))