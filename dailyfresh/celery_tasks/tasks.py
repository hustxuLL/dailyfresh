from celery import Celery
import time
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader, RequestContext


# 创建Celery对象
# 这里在同一个电脑启动redis 127.0.0.1:6379  127.0.0.1:6379/5
# app = Celery('celery_tasks/tasks',broker='redis://127.0.0.1:6379/5')
app = Celery('celery_tasks/tasks',broker='redis://192.168.52.129:6379/8')

# 定义一个celery任务函数 , 可以接受参数 也可以不接受参数，看需求
# 这里定义一个发送邮件 还是用django的send_mail()函数
# 需要用Celery实例对象app的task方法进行装饰

# celery 任务处理者端 需要的django项目的配置和初始化
# 在同一个电脑，可以加上这4行代码 那么celery任务发起者和处理者 就可以共享一份代码
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
django.setup()

from goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
from django_redis import get_redis_connection
from utils.mixin import LoginRequireMixin

@app.task
def send_register_active_email(to_email, username, token):
    '''celery发送邮件'''
    # 发送邮件 是通过django内置 send_mail()函数
    # send_mail()参数 5个重要的参数
    subject = '天天生鲜欢迎您'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1> 请点击下面的链接激活您的账号<br/>' \
                   '<a href= "http://127.0.0.1:8000/user/active/%s">"http://127.0.0.1:8000/user/active/%s"</a>' % (
                   username, token, token)

    # 发送邮件
    send_mail(subject, message, sender, receiver, html_message=html_message)

    # # 休眠5s
    # time.sleep(5)


# 生成index静态页面
@app.task
def generate_static_index_html():
    '''产生首页静态页面'''
    # 获取商品的种类信息
    types = GoodsType.objects.all()

    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:  # GoodsType
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

        # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = title_banners


    # 组织模板上下文
    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners}

    # 使用模板
    # 1.加载模板文件,返回模板对象
    temp = loader.get_template('static_index.html')
    # 2.模板渲染
    static_index_html = temp.render(context)

    # 生成首页对应静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)


