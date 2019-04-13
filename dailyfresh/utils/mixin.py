from django.contrib.auth.decorators import login_required


class LoginRequireMixin(object):
    ''' 让模型类继承，对相应的视图函数进行用户登录装饰'''
    @classmethod
    def as_view(cls, **initkwargs):
        # 调用父类的as_view()方法
        view=super(LoginRequireMixin, cls).as_view(**initkwargs)
        # 完成装饰
        return login_required(view)