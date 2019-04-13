from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
import re
from user.models import User,Address,AddressManager
from goods.models import GoodsSKU
from order.models import OrderInfo,OrderGoods
from django.core.paginator import Paginator

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import send_mail
import time
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate,login,logout
from utils.mixin import LoginRequireMixin
from redis import StrictRedis
from django_redis import get_redis_connection



# Create your views here.

# /user/register
def register(request):
    '''显示注册页面'''

    if request.method == 'GET':
        return render(request, 'register.html')
    # 下面是POST提交 即登录页面的处理
    else:
        '''进行注册处理'''
        # 接受数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        # 注意{'errmsg': '数据不完整'} 这一块部分是上下文 需要传给模板变量
        # 后端是否接受到用户注册输入的数据
        if not all([username, password, cpwd, email]):
            # 数据不完整,返回注册页面，并报出errmsg 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 检验两次密码是否一样
        if password != cpwd:
            # 密码输入两次不一样的
            return render(request, 'register.html', {'errmsg': '两次密码不一样'})

        # 检验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            # 若邮箱格式不正确
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 检查用户是否勾选同意协议,用户勾选的话,allow值为on
        if allow != 'on':
            # 用户没有勾选，注册也失败
            return render(request, 'register.html', {'errmsg': '没有勾选同意协议'})

        # 由于django默认的用户认证系统，用户名重复，点击注册后，会报错
        # 所以在用户名重复时，也需要跳转到注册页面
        # get 查询操作，是返回一个查询集，只能查询一个，若没有或者多个都会抛异常的
        try:
            user1 = User.objects.get(username=username)
        except User.DoesNotExist:
            # 若抛出DoesNotExist异常 说明 查询失败，即用户名没有重复
            user1 = None

        if user1:
            # 若user有结果，说明用户名重复，需要直接返回注册页面
            return render(request, 'register.html', {'errmsg': '用户名重复注册'})

        # 当然邮箱 注册也要唯一，这里只是为了测试方便就没有写

        # 若以上都通过,则用户注册成功,就需要在后台对用户进行注册,即添加到数据库了
        # 这里使用django内置的用户认证,注册用户方法
        # (username, email, password) 参数顺序不能变
        user = User.objects.create_user(username, email, password)
        # django默认用户认证系统是直接激活,我们需要通过邮箱验证激活,所以设置为0
        user.is_active = 0
        # 保存
        user.save()



        # 这里跳转到主页,是产品经理都设计好的,开发时,根据文档来做就可以
        # 返回应答
        # 注意 redirect重定向反向解析 goods：index 之间不能有空格的
        return redirect(reverse('goods:index'))


def register_handle(request):
    '''进行注册处理'''
    # 接受数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    cpwd = request.POST.get('cpwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')


    # 进行数据校验
    # 注意{'errmsg': '数据不完整'} 这一块部分是上下文 需要传给模板变量
    # 后端是否接受到用户注册输入的数据
    if not all([username, password, cpwd, email]):
        # 数据不完整,返回注册页面，并报出errmsg 数据不完整
        return render(request, 'register.html', {'errmsg': '数据不完整'})

    # 检验两次密码是否一样
    if password != cpwd:
        # 密码输入两次不一样的
        return render(request, 'register.html', {'errmsg':'两次密码不一样'})

    # 检验邮箱
    if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        # 若邮箱格式不正确
        return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

    # 检查用户是否勾选同意协议,用户勾选的话,allow值为on
    if allow != 'on':
        # 用户没有勾选，注册也失败
        return render(request, 'register.html', {'errmsg': '没有勾选同意协议'})

    # 由于django默认的用户认证系统，用户名重复，点击注册后，会报错
    # 所以在用户名重复时，也需要跳转到注册页面
    # get 查询操作，是返回一个查询集，只能查询一个，若没有或者多个都会抛异常的
    try:
        user = User.objects.get(username=username)

    # 注意这里了别写错了，是User模型类，而不是user
    except User.DoesNotExist:
        # 若抛出DoesNotExist异常 说明 查询失败，即用户名没有重复
        user = None

    if user:
        # 若user有结果，说明用户名重复，需要直接返回注册页面
        return render(request, 'register.html', {'errmsg':'用户名重复注册'})

    # 当然邮箱 注册也要唯一，这里只是为了测试方便就没有写

    # 若以上都通过,则用户注册成功,就需要在后台对用户进行注册,即添加到数据库了
    # 这里使用django内置的用户认证,注册用户方法
    # (username, email, password) 参数顺序不能变
    user= User.objects.create_user(username, email, password)
    # django默认用户认证系统是直接激活,我们需要通过邮箱验证激活,所以设置为0
    user.is_active = 0
    # 保存
    user.save()
    # 这里跳转到主页,是产品经理都设计好的,开发时,根据文档来做就可以


    # 数据处理

    # 返回应答
    # 注意 redirect重定向反向解析 goods：index 之间不能有空格的
    return redirect(reverse('goods:index'))


class RegisterView(View):
    '''类视图'''
    def get(self,request):
        return render(request, 'register.html')

    def post(self,request):
        '''进行注册处理'''
        # 接受数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        # 注意{'errmsg': '数据不完整'} 这一块部分是上下文 需要传给模板变量
        # 后端是否接受到用户注册输入的数据
        if not all([username, password, cpwd, email]):
            # 数据不完整,返回注册页面，并报出errmsg 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 检验两次密码是否一样
        if password != cpwd:
            # 密码输入两次不一样的
            return render(request, 'register.html', {'errmsg': '两次密码不一样'})

        # 检验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            # 若邮箱格式不正确
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 检查用户是否勾选同意协议,用户勾选的话,allow值为on
        if allow != 'on':
            # 用户没有勾选，注册也失败
            return render(request, 'register.html', {'errmsg': '没有勾选同意协议'})

        # 由于django默认的用户认证系统，用户名重复，点击注册后，会报错
        # 所以在用户名重复时，也需要跳转到注册页面
        # get 查询操作，是返回一个查询集，只能查询一个，若没有或者多个都会抛异常的
        try:
            user = User.objects.get(username=username)

        # 注意这里了别写错了，是User模型类，而不是user
        except User.DoesNotExist:
            # 若抛出DoesNotExist异常 说明 查询失败，即用户名没有重复
            user = None

        if user:
            # 若user有结果，说明用户名重复，需要直接返回注册页面
            return render(request, 'register.html', {'errmsg': '用户名重复注册'})

        # 当然邮箱 注册也要唯一，这里只是为了测试方便就没有写

        # 若以上都通过,则用户注册成功,就需要在后台对用户进行注册,即添加到数据库了
        # 这里使用django内置的用户认证,注册用户方法
        # (username, email, password) 参数顺序不能变
        user = User.objects.create_user(username, email, password)
        # django默认用户认证系统是直接激活,我们需要通过邮箱验证激活,所以设置为0
        user.is_active = 0
        # 保存
        user.save()

        # 发送激活邮件，包含激活链接: http://127.0.0.1:8000/user/active/3
        # 激活链接中需要包含用户的身份信息, 并且要把身份信息进行加密
        # 首先要对用户id进行加密
        # 创建一个Serializer类对象
        serializer = Serializer(settings.SECRET_KEY, 3600)
        # 要加密的用户id
        info = {'confirm': user.id}
        # 加密后的结果 结果是bytes字符串 需要进行解码
        token = serializer.dumps(info)
        # decode() 默认是utf8解码 所以不需要传入参数
        token = token.decode()

        # 注释掉下面的
        # # 发送邮件 是通过django内置 send_mail()函数
        # # send_mail()参数 5个重要的参数
        # subject = '天天生鲜欢迎您'
        # message = ''
        # sender = settings.EMAIL_FROM
        # receiver = [email]
        # html_message = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1> 请点击下面的链接激活您的账号<br/>' \
        #                '<a href= "http://127.0.0.1:8000/user/active/%s">"http://127.0.0.1:8000/user/active/%s"</a>'%(username, token, token)
        #
        # # 发送邮件
        # send_mail(subject, message, sender, receiver, html_message = html_message)

        # 通过celery来发邮件
        send_register_active_email.delay(email, username, token)


        # 这里跳转到主页,是产品经理都设计好的,开发时,根据文档来做就可以
        # 返回应答
        # 注意 redirect重定向反向解析 goods：index 之间不能有空格的

        # 设置休眠对比看 celery的优势
        # 设置了休眠，就会阻塞5s后再跳转后首页的,在注册页面 等待5s后跳转的
        # time.sleep(5)

        return redirect(reverse('goods:index'))


class ActiveView(View):
    '''用户激活'''
    def get(self, request, token):
        # 用户点击激活链接，接受到加密后的token需要进行解密
        # 创建同样的秘钥
        serializer = Serializer(settings.SECRET_KEY, 3600)
        # 解密超时 会抛出异常 所以需要try
        try:
            # 若没有异常，则可以解密
            # info = {'confirm': user.id}
            info = serializer.loads(token)
            user_id = info['confirm']

            # 需要通过用户id来查找用户对象
            # 这里 不是== 符号
            user = User.objects.get(id=user_id)
            # 设置用户为已经激活状态
            user.is_active = 1
            # 修改了还需要save保存
            user.save()
            # 用户注册成功切激活，直接跳转到登录页面
            # 这里要重定向redirect 和使用反向解析reverse
            return redirect(reverse('user:login'))

        except SignatureExpired as e:
            # 若超时，则直接返回一个HttpRespose对象，这里简单返回一个字符串 激活链接超时
            # 在实际项目中，需要给用户再发一个链接，用户点击这个链接，邮箱就可以再收到一个激活链接
            return HttpResponse('激活链接超时')


class LoginView(View):

    def get(self, request):
        '''显示用户登录'''

        # 由于设置了记住用户名的cookie
        # 在下次登录，需要判断浏览器发起的请求里面是否有相应的cookie
        if 'username' in request.COOKIES:
            # 若有，则需要读取
            username = request.COOKIES.get('username')
            # 并需要设置勾选框
            checked = 'checked'
        else:
            # 若没有，传给模板变量的vlaue值对应为空字符串
            username =''
            checked = ''

        # 模板上下文
        contexts={'username': username,
                 'checked': checked}

        return render(request, 'login.html', contexts)

    def post(self, request):
        '''处理用户登录信息'''
        '''
        处理用户登录信息，有两种情况，因为表单post提交，没有设置action
        所以action默认就对应的页面的地址栏---即登录页面url地址栏 
        地址栏传递参数是通过get获取的
        要通过get方法来看是否能获取到next参数
        而get读取参数
        失败，则返回none，可以给它一个默认值，即跳转到首页 reverse('goods:index')
        成功，则返回‘/user’，即跳转到用户中心页面
        1 http://127.0.0.1:8000/user/login 这个是不能 这个是默认的正常情况下跳转到网站首页
        2 http://127.0.0.1:8000/user/login?next=/user/ 这个是可以获取参数next ---跳转到用户中心
        
        上面都是建立在 用户账号和密码校验正确的情况下
        '''

        # 接受数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')

        # 校验数据
        # 判断接受数据是否完整
        if not all([username, password]):
            # 若数据接受不完整，直接返回登录页面，提示用户名和密码没有输入
            return render(request, 'login.html', {'errmsg':'用户名或密码没有输入'})


        # 业务处理
        # 验证用户名和密码是否正确
        # 这里使用django内置用户认证系统
        # 若查到则返回一个User模型类对象
        user=authenticate(username=username, password=password)

        if user is not None:
            # 即在数据库中找到对应的用户名和密码

            # 还需要判断用是否激活
            if user.is_active:
                # 用户已经激活
                # 登录成功，在返回主页之前，不需要保存用户的session信息
                # 保存用户的session信息，也是用django内置的认证系统 login(request,user)
                # 记录用户的登录状态
                login(request, user)

                # 在设置cookie 之前需要 HttpResponse对象或者子类对象
                response = redirect(reverse('goods:index'))
                # 判断用户是否勾选记住用户名
                if remember == 'on':
                    # 就需要设置cookie信息来记住用户名
                    response.set_cookie('username',username,max_age=7*24*3600)
                else:
                    # 若用户登录没有勾选，则还需要删除浏览器中的cookie
                    response.delete_cookie('username')

                # 在用户名和密码正确情况下
                # 再看能否获取到表单action发起get请求方式的参数 next,并设置默认只为首页
                next_url = request.GET.get('next', reverse('goods:index'))

                # 返回应答
                return redirect(next_url)

                # 之后就跳转主页 反向解析 返回应答
                # return response
                # return redirect(reverse('goods:index'))
            else:
                return render(request, 'login.html', {'errmsg': '用户没有激活'})
        else:
            # 否则，用户名 密码错误
            # 直接返回登录页面
            return render(request, 'login.html', {'errmsg':'用户名密码错误'})


    # 下面是没有设置cookie记录用户名
    # def post(self, request):
    #     '''处理用户登录信息'''
    #
    #     # 接受数据
    #     username = request.POST.get('username')
    #     password = request.POST.get('pwd')
    #     remember = request.POST.get('remember')
    #
    #     # 校验数据
    #     # 判断接受数据是否完整
    #     if not all([username, password]):
    #         # 若数据接受不完整，直接返回登录页面，提示用户名和密码没有输入
    #         return render(request, 'login.html', {'errmsg':'用户名或密码没有输入'})
    #
    #
    #     # 业务处理
    #     # 验证用户名和密码是否正确
    #     # 这里使用django内置用户认证系统
    #     # 若查到则返回一个User模型类对象
    #     user=authenticate(username=username, password=password)
    #
    #     if user is not None:
    #         # 即在数据库中找到对应的用户名和密码
    #
    #         # 还需要判断用是否激活
    #         if user.is_active:
    #             # 用户已经激活
    #             # 登录成功，在返回主页之前，不需要保存用户的session信息
    #             # 保存用户的session信息，也是用django内置的认证系统 login(request,user)
    #             # 记录用户的登录状态
    #             login(request, user)
    #
    #             # 之后就跳转主页 反向解析 返回应答
    #             return redirect(reverse('goods:index'))
    #         else:
    #             return render(request, 'login.html', {'errmsg': '用户没有激活'})
    #     else:
    #         # 否则，用户名 密码错误
    #         # 直接返回登录页面
    #         return render(request, 'login.html', {'errmsg':'用户名密码错误'})

class LogoutView(View):
    '''用户退去登录'''
    def get(self, request):

        # 直接调用django内置用户认证系统logout()
        logout(request)
        # 用户退去登录，跳转到网站首页
        return redirect(reverse('goods:index'))


# /user
# 用户中心三个页面，需要继承LoginRequireMixin类，装饰判断用户是否登录
class UserInfoView(LoginRequireMixin, View):
    '''用户中心--个人信息页'''
    def get(self, request):

        # 获取用户登录的user
        user = request.user

        # 获取用户默认地址信息
        address = Address.objects.get_default_address(user)

        # 历史浏览记录--是存储在redis数据库，格式是list，key是history_user.id
        # 链接redis数据库，创建一个StrictRedis对象,需要三个参数 127.0.0.1:6379/5
        # 创建一个StrictRedis对象sr，就可以用sr来操作redis数据库5中数据格式的命令
        # sr = StrictRedis(host='127.0.0.1', port=6379, db=5)

        # 这里用django-redis包 原生客户端使用 get_redis_connection()
        # get_redis_connection()参数'default' 这个是setting里面对redis数据库的配置 里面包含了 需要三个参数 127.0.0.1:6379/5
        # get_redis_connection()返回只也是一个StrictRedis对象，所以和上面是等效的
        con = get_redis_connection('default')

        # redis存储用户历史浏览记录的数据格式是list　
        # redis存储用户历史浏览记录的数据 对应的key 设置为history_user.id  key对应vlaue是用户浏览过的商品id
        history_key = 'history_%d' % user.id
        # 在redis数据库，根据list格式的key取值  范围取值 lrange key start stop
        # 这里假设 list数据格式 key为history_user.id 对应的value的值的插入方式是lpush 即从左侧插入---用户访问一个商品详情页就会把对应商品id插入到列表中
        # 下面就是取出前5个商品id
        sku_ids = con.lrange(history_key, 0, 4)
        # 由于要拿到前5个商品的SKU对象，所以这里要通过前5个商品id来查找到对应的商品的SKU
        # 那就好遍历sku_ids列表，一个一个找对应的SKU对象

        # 存储查询到商品SKU
        goods_li = []
        for sku_id in sku_ids:
            goods = GoodsSKU.objects.get(id=sku_id)
            goods_li.append(goods)

        # 组织上下文
        contests={'page':'user',
                  'address': address,
                  'goods_li': goods_li}

        # return render(request, 'user_center_info.html')
        # 鼠标点击对应页面地址才会高亮显示，设置一个上下文page
        # contests={'page':'user',
        #           'address': address}
        return render(request, 'user_center_info.html', contests)


# /user/order
# 用户中心三个页面，需要继承LoginRequireMixin类，装饰判断用户是否登录
# /user/order
class UserOrderView(LoginRequireMixin, View):
    '''用户中心-订单页'''
    def get(self, request, page):
        '''显示'''
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count*order_sku.price
                # 动态给order_sku增加属性amount,保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

        # 分页
        paginator = Paginator(orders, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page':order_page,
                   'pages':pages,
                   'page': 'order'}

        # 使用模板
        return render(request, 'user_center_order.html', context)


# /user/address
# 用户中心三个页面，需要继承LoginRequireMixin类，装饰判断用户是否登录
class AddressView(LoginRequireMixin, View):
    '''用户中心--地址页'''

    def get(self, request):

        # return render(request, 'user_center_site.html')
        # 鼠标点击对应页面地址才会高亮显示，设置一个上下文page

        # 考虑到要显示默认地址，所以先要在地址表中查询看是否有默认地址，这里和post里面是一样的操作
        user = request.user

        # 使用自定义管理器
        address = Address.objects.get_default_address(user)

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None

        # address 不需要在这里判断，而是传给模板文件，里面进行if判断
            # 说明有该用户在地址表中有默认地址，就要把Address类对象传给模板文件
        contests = {'page': 'address',
                    'address': address}

        return render(request, 'user_center_site.html', contests)


    def post(self, request):
        '''处理用户中心页面表单post提交'''

        # 接受用户表单输入的地址信息参数
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 地址信息数据校验---要合法
        # 1是否接受到数据 all方法判断
        if not all([receiver, addr, zip_code, phone]):
            # 接受数据不完整，返回用户中心地址页面，重写输入
            contexts = {'errmsg': '数据不完整'}
            return render(request, 'user_center_site.html', contexts)
        # 2 检验手机号格式
        if not re.match(r'^1[3458]\d{9}$',phone):
            # 手机号码格式不对
            contexts = {'errmsg': '手机号码格式不对'}
            return render(request, 'user_center_site.html', contexts)

        # 业务处理，更新用户模块中地址表
        # 地址表中的is_default 属性需要判断，
        # 即找该用户所对应多条地址数据，有没有默认的地址，因为默认地址只有1个
        # 若有，则此次更新的地址表数据的is_default 为false
        # 若没有，则此次更新的地址表数据的is_default 为true

        # 要查找，需要两个地址表的两个属性 1user为当前登录用户 2is_default为true
        # 而当前 user 可以通过django用户认证系统得到,request.user一定是User类一个实例，因为用户已经登录了
        user = request.user
        # get查找
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 没有找到，说明目前用户还没有设置默认地址
        #     address = None

        # 使用自定义管理器
        # 下面写是错的，两个类是两个独立的空间，
        # 要想联系起来，需要再一个类中定义定义另一个类的实例对象
        # 再调用另一个类实例对象的方法
        # address = AddressManager.get_default_address(user)
        address = Address.objects.get_default_address(user)
        # 对查询结果判断，来设置要添加地址信息的is_default属性
        if address:
            is_default = False
        else:
            is_default = True

        # 到这就可以给地址表更新数据
        Address.objects.create(user=user,
                               addr=addr,
                               receiver=receiver,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        # 返回应答，这里就是在页面刷新，即点击提交后刷新上面默认地址
        return redirect(reverse('user:address'))

