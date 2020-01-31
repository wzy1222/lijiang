# coding: utf-8
import json
import os
from datetime import datetime
import logging
from enum import Enum, IntEnum

from flask import Flask
from flask_admin import Admin
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user
from markupsafe import Markup
from werkzeug.routing import ValidationError

from config import dev
from config import online
from flask_sqlalchemy import SQLAlchemy
import requests

from flask_babelex import Babel
from flask_migrate import Migrate


is_debug = os.environ.get('LIJIANG_DEBUG')

app = Flask(__name__)
if is_debug:
    app.config.from_object(dev)
else:
    app.config.from_object(online)


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(message)s')

babel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
admin = Admin(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


login_manager = LoginManager()
login_manager.init_app(app)


class UserTypeEnum(Enum):
    user = 0
    admin = 1


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(128))
    tag_id = db.Column(db.BIGINT, nullable=True)
    type = db.Column(db.Integer, nullable=False, default=UserTypeEnum.user.value)


class Commodity(db.Model):
    __tablename__ = 'commodity'

    item_id = db.Column(db.BIGINT, primary_key=True)
    detail_url = db.Column(db.String(512))
    image = db.Column(db.String(512))
    price = db.Column(db.Integer)
    title = db.Column(db.String(512))


class Tag(db.Model):
    __tablename__ = 'tag'

    tag_id = db.Column(db.BIGINT, primary_key=True)
    name = db.Column(db.String(512))


class AdminCommand(db.Model):
    __tablename__ = 'admin_command'

    class Command(IntEnum):
        default_command = 0
        sync_item = 1
        sync_tag = 2

    class Status(IntEnum):
        failure = 0
        success = 1

    id = db.Column(db.BIGINT, primary_key=True)
    command = db.Column(db.INTEGER, nullable=False)
    reason = db.Column(db.VARCHAR(255), nullable=False)
    extra = db.Column(db.TEXT)
    create_time = db.Column(db.DATETIME, nullable=False, default=datetime.now),
    status = db.Column(db.INTEGER, nullable=False)



@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    return user


import logging
from flask import render_template, request, session, redirect, url_for
import random
from app import app


class BaseModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated


class AdminModelView(BaseModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.type == UserTypeEnum.admin.value


class TagModelView(AdminModelView):
    can_create = False
    can_delete = False
    can_edit = False

    column_list = ('tag_id', 'name')
    column_searchable_list = ('tag_id', 'name')


class UserModelView(AdminModelView):
    can_create = True
    can_edit = True
    can_delete = True

    column_labels = {
        'tag_id': '我关联的商品分组',
        'type': '用户类型',
    }

    column_formatters = {
        'type': lambda v, c, m, n: UserTypeEnum(m.type)
    }


class CommodityModelView(BaseModelView):
    can_create = False
    can_delete = False
    can_edit = False

    column_list = ('item_id', 'title', 'price', 'image', 'detail_url')
    column_searchable_list = ('title', )

    column_labels = {
        'item_id': 'id',
        'title': '名称',
        'price': '价格',
        'image': '图片',
        'detail_url': '详情'
    }

    column_formatters = {
        'price': lambda v, c, m, n: m.price/100.0,
        'image': lambda v, c, m, n: Markup(f'<img src={m.image} alt="" style="width: 75px; height: 75px">'),
        'detail_url': lambda v, c, m, n: Markup(f'<a href="{m.detail_url}">查看详情</a>')
    }

    @action('add_tag', '添加到我的分组', '确认？')
    def add_tag(self, item_ids):
        logging.info(f'items = {item_ids}')

        for item_id in item_ids:
            add_item_tag(int(item_id), current_user.tag_id)
        logging.info(f'add tag ok')


class AdminCommandModelView(AdminModelView):
    can_delete = False
    can_edit = False

    column_display_pk = True

    column_sortable_list = ('id', )

    column_labels = {
        'id': 'ID',
        'command': '指令',
        'reason': '原因',
        'extra': '参数',
        'create_time': '时间',
        'status': '状态',
    }

    column_default_sort = ('id', True)

    form_choices = column_choices = {
        'command': [
            # todo 此处添加命令对应的选项文字
            (AdminCommand.Command.default_command.value, '默认命令'),
            (AdminCommand.Command.sync_item.value, '重置商品'),
            (AdminCommand.Command.sync_tag.value, '重置标签')

        ],
        'status': [
            (AdminCommand.Status.success.value, '成功'),
            (AdminCommand.Status.failure.value, '失败')
        ],
    }

    column_formatters = {
        'extra': lambda c, v, m, d: Markup(f'<pre>{m.extra}</pre>')
    }

    form_args = {
        'command': {"coerce": int},
    }

    form_rules = ('command', 'reason', 'extra')

    def on_model_change(self, form, model: AdminCommand, is_created):
        logging.info(f"form = {form}, model = {model}, is_created = {is_created}")
        model.status = AdminCommand.Status.success.value

        if model.command == AdminCommand.Command.sync_item.value:
            try:
                extra_json = json.loads(model.extra)
                tag_ids = extra_json['tag_ids']
            except Exception:
                valid_extra_format = {
                    "tag_ids": [1, 2]
                }
                raise ValidationError('参数不合法，合法参数格式如下：' + json.dumps(valid_extra_format))

            if not tag_ids:
                raise ValidationError('参数不允许为空')

            nums_deleted = Commodity.query.delete()
            logging.info(f"item deleted, nums_deleted = {nums_deleted}")
            sync_items_by_tag_ids(tag_ids)

            db.session.commit()
            return

        if model.command == AdminCommand.Command.sync_tag.value:
            nums_deleted = Tag.query.delete()
            logging.info(f"tag deleted, nums_deleted = {nums_deleted}")
            sync_tags()
            db.session.commit()
            return

        return


admin.add_view(UserModelView(User, db.session, name="用户"))
admin.add_view(CommodityModelView(Commodity, db.session, name="商品"))
admin.add_view(TagModelView(Tag, db.session, name="标签分组"))
admin.add_view(AdminCommandModelView(AdminCommand, db.session, name="管理员命令"))


@app.route('/')
@login_required
def index():
    return redirect(url_for('admin.index'))


@app.route('/token/')
@login_required
def get_access_token():

    body = dict(client_id='fd7df0db64be49e4d8',
                client_secret='481efe13a004c697a7296d0fde182f64',
                authorize_type='silent',
                grant_id=42855133
                )

    resp = requests.post('https://open.youzanyun.com/auth/token', json=body)
    logging.info(f"resp = {resp}, json = {resp.json()}")

    results = resp.json()
    datas = results.get('data')
    access_token = datas.get('access_token')

    return access_token


def pakage_url(url):
    access_token = get_access_token()
    return f"{url}?access_token={access_token}"


def sync_items_by_tag_ids(tag_ids):
    items = []

    for tag_id in tag_ids:
        for page_id in range(1, 100):
            url = pakage_url('https://open.youzanyun.com/api/youzan.showcase.render.api.listGoodsByTagId/1.0.0')
            headers = {'content-type':'application/json'}
            page_size = 2
            body = dict(page=page_id, page_size=page_size, tag_id=tag_id)
            resp = requests.post(url, headers=headers, json=body)
            logging.info(f"resp = {resp}, json = {resp.json()}")
            results = resp.json()
            datas = results.get("data").get("list")
            items.extend(datas)

            if len(datas) < page_size:
                break

    ids = set()

    for item in items:
        if item["id"] in ids:
            continue

        url = pakage_url('https://open.youzanyun.com/api/youzan.item.get/3.0.0')
        url += f'&item_id={item["id"]}'

        headers = {'content-type':'application/json'}
        resp = requests.get(url, headers=headers)
        logging.info(f"resp = {resp}, json = {resp.json()}")
        results = resp.json()

        commodity = Commodity()
        commodity.item_id = item.get("id")
        commodity.detail_url = results.get("data").get("item").get("detail_url")
        commodity.image = item.get("image_url")
        commodity.price = item.get("price")
        commodity.title = item.get("title")
        db.session.add(commodity)
        ids.add(commodity.item_id)

    logging.info(f"add items ok, len = {len(items)}")

    return results


@app.route('/tags/create/<tag_name>/')
@login_required
def create_tag(tag_name):
    url = pakage_url('https://open.youzanyun.com/api/youzan.itemcategories.tag.add/3.0.0')
    headers = {'content-type':'application/json'}
    body = dict(name=tag_name)
    resp = requests.post(url, headers=headers, json=body)
    logging.info(f"resp = {resp}, json = {resp.json()}")
    results = resp.json()

    return results


def sync_tags():
    url = pakage_url('https://open.youzanyun.com/api/youzan.itemcategories.tags.get/3.0.0')
    headers = {'content-type':'application/json'}
    resp = requests.get(url, headers=headers)
    logging.info(f"resp = {resp}, json = {resp.json()}")
    results = resp.json()

    items = results.get("data").get("tags")
    for item in items:
        tag = Tag(tag_id=item.get("id"), name=item.get("name"))
        db.session.add(tag)
    logging.info(f"add tags ok, len = {len(items)}")

    return results


def add_item_tag(item_id, tag_id):
    url = pakage_url(f'https://open.youzanyun.com/api/youzan.item.get/3.0.0')
    headers = {'content-type':'application/json'}
    body = dict(item_id=item_id)
    resp = requests.post(url, headers=headers, json=body)
    logging.info(f"resp = {resp}, json = {resp.json()}")
    results = resp.json()

    tag_ids = results.get("data").get("item").get("tag_ids")
    tag_ids = ','.join(map(str, tag_ids))
    tag_ids += f",{tag_id}"

    url = pakage_url('https://open.youzanyun.com/api/youzan.item.update/3.0.1')
    headers = {'content-type':'application/json'}
    body = dict(item_id=item_id, tag_ids=tag_ids)
    logging.info(f"body = {body}")
    resp = requests.post(url, headers=headers, json=body)
    logging.info(f"resp = {resp}, json = {resp.json()}")
    results = resp.json()

    return results


@app.route('/login/', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/login/auth/', methods=['POST'])
def auth():
    email = request.form['email'].strip()
    password = request.form['password'].strip()

    user = User.query.filter(User.password == password, User.email == email).first()
    if not user:
        return redirect(url_for('login'))

    login_user(user)
    return redirect(url_for('admin.index'))


@app.route('/logout/')
@login_required
def logout():
    session.clear()
    return "logout done"


if __name__ == '__main__':
    app.run()
