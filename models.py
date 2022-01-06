import pymysql
from flask import session
import os

database = pymysql.connect(user='admin', host=os.environ['DB_HOST'],password=os.environ['DB_PASSWORD'])
cursor = database.cursor(pymysql.cursors.DictCursor)
sql = '''use photogallery'''
cursor.execute(sql)





class UserModel:
    def __init__(self, name=None, email=None, password=None, id=None):
        self.name = name
        self.email = email
        self.password = password
        self.id = id

    def save(self):
        query= f"INSERT INTO user (name, email, password) VALUES ('{self.name}','{self.email}','{self.password}')"
        cursor.execute(query)
        database.commit()

    @staticmethod
    def fetch(email):
        cursor.execute('select * from user where email= %s', (email))
        data = cursor.fetchone()
        if data:
            return UserModel(name=data['name'], email=data['email'], password=data['password'], id=data['id'])

class ImageModel:
    def __init__(self, path=None, user_id=None, caption=None, id=None):
        self.path=path
        self.user_id=user_id
        self.caption=caption
        self.id=id

    def save(self):
        query=f"insert into userimages (user_id, path, caption) values ({self.user_id}, '{self.path}', '{self.caption}')"
        cursor.execute(query)
        database.commit()

    @staticmethod
    def fetchall(user_id):
        cursor.execute('select * from userimages where user_id=%s',(user_id))
        data=cursor.fetchall()
        result=[]
        if data:
            for image in data:
                image_instance=ImageModel(path=image["path"], user_id=image["user_id"], caption=image["caption"],id=image["id"])
                result.append(image_instance)
        return result

    @staticmethod
    def fetchtaggedimages(user_id):
        cursor.execute(f"select * from taggedimages where user_id={user_id}")
        data = cursor.fetchall()
        list_of_image_dicts=[]
        result=[]       #list of image instaces
        if data:
            for image in data:
                cursor.execute(f"select * from userimages where id={image['image_id']}")
                d=cursor.fetchone()
                list_of_image_dicts.append(d)

            for image in list_of_image_dicts:
                image_instance = ImageModel(path=image["path"], user_id=image["user_id"], caption=image["caption"],id=image["id"])
                result.append(image_instance)
        return result

# class TaggedImageModel:
#     def __init__(self, user_id=None, image_id=None, id=None):
#         self.user_id=user_id
#         self.image_id=image_id
#         self.id=id
#
#     @staticmethod
#     def fetchtaggedimages(user_id):
#         cursor.execute(f"select * from taggedimages where user_id={user_id}")
#         data=cursor.execute()
#         result=[]
#         if data:
#             for image in data:
#                 tagged_image_instace=TaggedImageModel(user_id=image["user_id"], image_id=image["image_id"], id=image["id"])
#                 result.append(tagged_image_instace)
#         return result
