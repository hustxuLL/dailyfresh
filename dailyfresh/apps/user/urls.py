from django.conf.urls import url
# from user import views
from user.views import RegisterView,ActiveView,LoginView,UserInfoView,UserOrderView,AddressView,LogoutView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # url(r'^register$', views.register, name='register'), # 注册
    # url(r'^register_handle$', views.register_handle, name='register_handle'), # 注册处理

    url(r'^register$', RegisterView.as_view(), name='register'),  # 注册
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 激活
    url(r'^login$', LoginView.as_view(), name='login'),  # 登录
    url(r'^logout$', LogoutView.as_view(), name='logout'),  # 退去登录

    # 这里用户中心三个页面的url配置，写到这，还没到登录装饰器
    # url(r'^order$', UserOrderView.as_view(), name='order'),  # 用户中心--订单页
    # url(r'^address$', AddressView.as_view(), name='address'),  # 用户中心--地址页
    # url(r'^$', UserInfoView.as_view(), name='user'),  # 用户中心-个人信息页

    # 用django内置的用户认证系统，对用户是否登录判断进行装饰
    # 在用户没有登录访问/user 跳转到 http://127.0.0.1:8000/accounts/login/?next=/user/
    # LOGIN_URL=‘/accounts/login/’ 这是默认的配置 django认证系统里
    # 需要修改 即用户未登录 需要跳转到登录页面
    # 在项目setting中配置 LOGIN_URL= ‘/user/login’
    # 再次运行 用户未登录 访问用户中心页面，就会跳转到 http://127.0.0.1:8000/user/login?next=/user/
    # url(r'^order$', login_required(UserOrderView.as_view()), name='order'),  # 用户中心--订单页
    # url(r'^address$', login_required(AddressView.as_view()), name='address'),  # 用户中心--地址页
    # url(r'^$', login_required(UserInfoView.as_view()), name='user'),  # 用户中心-个人信息页

    # 若对每个视图类都这么装饰，太麻烦了，把这个装饰封装到类中，再在定义视图类时直接继承
    # 这样 在配置url时还是原来的视图类名.as_view()
    url(r'^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),  # 用户中心-订单页
    url(r'^address$', AddressView.as_view(), name='address'),  # 用户中心--地址页
    url(r'^$', UserInfoView.as_view(), name='user'),  # 用户中心-个人信息页

]
