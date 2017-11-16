import time

from bson import ObjectId
from pymongo import MongoClient

from utils import log


class Model(object):
    db = MongoClient()['web21']

    @classmethod
    def valid_names(cls):
        names = [
            # (字段名, 类型, 默认值)
            ('deleted', bool, False),
            ('created_time', int, 0),
            ('updated_time', int, 0),
        ]
        return names

    def __repr__(self):
        class_name = self.__class__.__name__
        properties = ('{0} = {1}'.format(k, v) for k, v in self.__dict__.items())
        return '<{0}: \n  {1}\n>'.format(class_name, '\n  '.join(properties))

    @classmethod
    def new(cls, form, **kwargs):
        """
        new 是给外部使用的函数
        """
        # 创建一个空对象
        m = cls()

        for name in cls.valid_names():
            k, t, v = name
            if k in form:
                setattr(m, k, t(form[k]))
            else:
                # 设置默认值
                setattr(m, k, v)

        # 处理额外的参数 kwargs
        for k, v in kwargs.items():
            if hasattr(m, k):
                setattr(m, k, v)
            else:
                raise KeyError

        # 写入默认数据
        timestamp = int(time.time())
        m.created_time = timestamp
        m.updated_time = timestamp
        m.deleted = False
        m.save()
        return m

    def save(self):
        name = self.__class__.__name__
        print('save', self.__dict__)
        _id = self.db[name].save(self.__dict__)
        self.id = str(_id)

    @classmethod
    def delete(cls, id):
        name = cls.__name__
        query = {
            '_id': ObjectId(id),
        }
        values = {
            '$set': {
                'deleted': True
            }
        }
        cls.db[name].update_one(query, values)

    @classmethod
    def update(cls, id, form):
        name = cls.__name__
        query = {
            '_id': ObjectId(id),
        }
        values = {
            '$set': form,
        }
        log('mongo update', query, values)
        r = cls.db[name].update_one(query, values)

    @classmethod
    def _new_with_bson(cls, bson):
        """
        这是给内部 all 这种函数使用的函数
        从 mongo 数据中恢复一个 model
        """
        m = cls()
        print('bson', bson)
        for key in bson:
            setattr(m, key, bson[key])
        m.id = str(bson['_id'])
        return m

    @classmethod
    def all(cls):
        return cls._find()

    @classmethod
    def _find(cls, **kwargs):
        name = cls.__name__
        kwargs['deleted'] = False
        if 'id' in kwargs:
            kwargs['_id'] = ObjectId(kwargs['id'])
            kwargs.pop('id')
        ds = cls.db[name].find(kwargs)
        print('_find', kwargs, ds)
        l = [cls._new_with_bson(d) for d in ds]
        return l

    @classmethod
    def find_by(cls, **kwargs):
        return cls.find_one(**kwargs)

    @classmethod
    def find_all(cls, **kwargs):
        return cls._find(**kwargs)

    @classmethod
    def find(cls, id):
        return cls.find_one(id=id)

    @classmethod
    def find_one(cls, **kwargs):
        l = cls._find(**kwargs)
        if len(l) > 0:
            return l[0]
        else:
            return None

    def json(self):
        d = self.__dict__
        d.pop('_id')
        return d
