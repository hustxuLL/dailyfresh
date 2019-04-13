from haystack import indexes
# 导入要索引的模型类
from goods.models import GoodsSKU

# 指定对于某个类的某些数据建立索引
# 索引类命名格式 模型类名+Index


class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    # document=True 是索引要对字段建立
    # use_template=True  是 制定根据表中的那些字段建立索引文件的说明放在一个文件中，文件在模板下面
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return GoodsSKU

    def index_queryset(self, using=None):
        return self.get_model().objects.all()