from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings

class FDFSStorage(Storage):
    '''自定义文件存储类--上传到远程的fdfs分布式图片服务器'''

    def __init__(self, client_conf= None, nginx_path= None):

        if client_conf is None:
            # self.client_conf = './utils/fdfs/client.conf'
            self.client_conf = settings.FDFS_CLIENT_CONF

        if nginx_path is None:
            # self.nginx_path = 'http://192.168.52.129:8888/'
            self.nginx_path = settings.FDFS_URL


    # 自定义 需要重写父类Storage中的四个方法
    # open save exists url

    def open(self, name, mode='rb'):
        '''由于项目不需要打开文件，所以这里写pass'''
        pass

    def save(self, name, content):
        '''这个是主要的，保存django后台管理上传到fdfs'''
        # name 是文档id
        # content 是django file对象，可以通过read方法读取文件内容

        # 创建一个Fdfs_client 对象连接远程的fdfs
        client = Fdfs_client(self.client_conf)
        # 由于是使用文件内容上传
        # 所以调用这个方法 Fdfs_client 里面的 def upload_by_buffer(self, filebuffer, file_ext_name = None, meta_dict = None):

        # 上传文件到fdfs
        res = client.upload_appender_by_buffer(content.read())

        # 返回值是一个字典，里面包含
        '''
        return dict {
            'Group name'      : group_name,
            'Remote file_id'  : remote_file_id,
            'Status'          : 'Upload successed.',
            'Local file name' : '',
            'Uploaded size'   : upload_size,
            'Storage IP'      : storage_ip
        }
        '''
        # 对上传的结果进行判断，看是否成功上传
        if res.get('Status') != 'Upload successed.':
            # 不一样则上传失败，这里就抛出一个异常
            raise Exception('文件上传到fastfds失败')

        # 若没有抛出异常则上传成功
        # 'Remote file_id' 是fdfs Storage服务器返回给浏览器的文件id 需要保存的
        # 在模板页面进行宣传成 http://nginx服务器ip地址:8888/fdfs返回的文件id
        # 接受 文件id
        filename_id = res.get('Remote file_id')

        return filename_id

    def exists(self, name):

        # 这个是django里面判断文件是否可用的，若可以则返回False
        # 若这里不用django来存储文件，和django没关系，所以，文件都是可用的
        # 但这个函数是必须的，因为调用save之前会先调用exist
        return False

    def url(self, name):

        # return 'http://192.168.52.129:8888/' + name
        return self.nginx_path + name
