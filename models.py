import pymysql
from flask import session
import os

def get_connection():
    connection = pymysql.connect(user='admin',
                                 host=os.environ['DB_HOST'],
                                 password=os.environ['DB_PASSWORD'],
                                 database='photogallery',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection

class UserModel:
    def __init__(self, name=None, email=None, password=None, id=None):
        self.name = name
        self.email = email
        self.password = password
        self.id = id

    def save(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                query= f"INSERT INTO user (name, email, password) VALUES ('{self.name}','{self.email}','{self.password}')"
                cursor.execute(query)
            connection.commit()

    @staticmethod
    def fetch(email):
        with get_connection() as connection:
            with connection.cursor() as cursor:
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
        with get_connection() as connection:
            with connection.cursor() as cursor:
                query=f"insert into userimages (user_id, path, caption) values ({self.user_id}, '{self.path}', '{self.caption}')"
                cursor.execute(query)
            connection.commit()

    @staticmethod
    def fetchall(user_id):
        with get_connection() as connection:
            with connection.cursor() as cursor:
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
        with get_connection() as connection:
            with connection.cursor() as cursor:
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

class OauthModel:
    def __init__(self, id =None, user_id=None, provider=None, access_token=None, expires_in=None):
        self.id=id
        self.user_id=user_id
        self.provider=provider
        self.access_token=access_token
        self.expires_in=expires_in

    def save(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('select * from oauth where user_id=%s and provider=%s', (self.user_id, self.provider))
                data = cursor.fetchall()
                if data:
                    query=f"update oauth set access_token='{self.access_token}', expires_in={self.expires_in} where user_id={self.user_id}"
                    cursor.execute(query)
                else:
                    query=f'insert into oauth (user_id, provider, access_token, expires_in) VALUES ({self.user_id},"{self.provider}","{self.access_token}",{self.expires_in})'
                    cursor.execute(query)
            connection.commit()
    @staticmethod
    def fetchaccesstoken(user_id, provider):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                query=f" select * from oauth where user_id={user_id} and provider='{provider}'"
                cursor.execute(query)
                data=cursor.fetchone()
                if data:
                    return OauthModel(id=data['id'], user_id=data['user_id'], provider=data['provider'], access_token=data['access_token'], expires_in=data['expires_in'])
