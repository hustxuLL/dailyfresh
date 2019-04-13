from django.db import models
from django.contrib.auth.models import AbstractUser
from db.base_model import BaseModel
# Create your models here.

# 自定义地址模型类管理器
class AddressManager(models.Manager):
    # 查找用户user默认的地址对象
    def get_default_address(self, user):
        # 由于self 是AddressManager类对象，所以也具有model.Manager模型类管理器方法
        try:
            address = self.get(user=user, is_default=True)

        # self.model 可以获取模型管理对象所在的模型类名
        except self.model.DoesNotExist:
            address = None

        return address


class User(AbstractUser, BaseModel):
    '''用户模型类'''

    class Meta:
        db_table = 'df_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class Address(BaseModel):
    '''地址模型类'''

    user = models.ForeignKey('User', verbose_name='所属账户')
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    addr = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, null=True, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    # 创建一个自定义管理器对象
    objects = AddressManager()

    class Meta:
        db_table = 'df_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name

