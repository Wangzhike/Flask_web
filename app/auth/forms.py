# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64),
                                           Email()])
    # PasswordField 类表示属性为 type="password" 的 <input> 元素
    password = PasswordField(u'密码', validators=[DataRequired()])
    # BooleanField 类表示复选框
    remember_me = BooleanField(u'保持登录')
    submit = SubmitField(u'登录')


class RegisterForm(FlaskForm):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64),
                                            Email()])
    username = StringField(u'用户名', validators=[
        DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                              u'用户名只能包含字母、数字、点和下划线')])
    password = PasswordField(u'密码', validators=[DataRequired()])
    password2 = PasswordField(u'确认密码', validators=[
        DataRequired(), EqualTo('password', message=u'密码必须一致')])
    submit = SubmitField(u'注册')

    # 表单类如果定义了以 validate_ 开头且后面跟着字段名的方法，这个方法就和常规的验证函数一起调用
    def validate_email(self, field):
        # 自定义的验证函数要想表示验证失败，可以抛出 ValidationError 异常，其参数就是错误信息
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮箱地址已经被注册过')

    # 表单类如果定义了以 validate_ 开头且后面跟着字段名的方法，这个方法就和常规的验证函数一起调用
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'用户名已经存在')


# 对于忘记密码无法登录的用户，提供重置密码功能。但安全起见，有必要使用类似于确认账户时用到的令牌。
#   1. 用户请求重置密码后，程序会向用户注册时提供的电子邮件地址发送一封包含重设令牌的邮件
class PasswordResetRequestForm(FlaskForm):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64),
                                            Email()])
    submit = SubmitField(u'申请重置密码')


# 对于忘记密码无法登录的用户，提供重置密码功能。但安全起见，有必要使用类似于确认账户时用到的令牌。
#   2. 用户点击邮件中的链接，令牌验证后，会显示一个用于输入新密码的表单
class PasswordResetForm(FlaskForm):
    email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64),
                                            Email()])
    password = PasswordField(u'新密码', validators=[DataRequired()])
    password2 = PasswordField(u'确认密码', validators=[
        DataRequired(), EqualTo('password', message=u'密码必须一致')])
    submit = SubmitField(u'重置密码')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(u'旧密码', validators=[DataRequired()])
    password = PasswordField(u'新密码', validators=[DataRequired()])
    password2 = PasswordField(u'确认密码', validators=[
        DataRequired(), EqualTo('password', message=u'密码必须一致')])
    submit = SubmitField(u' 更改密码')


class ChangeEmailForm(FlaskForm):
    email = StringField(u'新邮箱', validators=[DataRequired(), Length(1, 64),
                                            Email()])
    password = PasswordField(u'密码', validators=[DataRequired()])
    submit = SubmitField(u'更改邮箱')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            # 自定义的验证函数要想表示验证失败，可以抛出 ValidationError 异常，其参数就是错误信息
            raise ValidationError(u'该邮箱已经被注册！')