from requests_oauthlib import OAuth1

import oauth_twitter
from models import *
from flask import Flask, render_template, redirect, request, session
from flask_session import Session
import traceback
from werkzeug.utils import secure_filename
import os
import boto3
import random
import urllib
import requests
from datetime import datetime,timedelta
import base64
import traceback


app = Flask(__name__)
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)
IMAGE_UPLOADS = 'C:\\Users\\LENOVO\\Documents\\project\\static\\images'
app.config['IMAGE_UPLOADS'] = IMAGE_UPLOADS
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def register_func(username, email, password):
    data = UserModel.fetch(email)
    if data:
        return "email already registered"
    else:
        user = UserModel(name=username, email=email, password=password)
        user.save()
        return "True"

def login_func(email, password):
    user = UserModel.fetch(email)
    if user and user.password == password:
        session['logged_in_user'] = user.id
        session['user_name']=user.name
        return True
    else:
        return False
def upload_an_image(image,filename,  des):
    random_num=random.randint(0,1000)
    bucket = 'photogallery-vangmayi'
    filename=f"{session['logged_in_user']}_{random_num}_{filename}"
    client = boto3.client('s3',
                          region_name='ap-south-1',
                          aws_access_key_id=os.environ['AWS_ACCESSKEY'],
                          aws_secret_access_key=os.environ['AWS_SECRETACCESSKEY'])
    result=client.put_object(Body=image,
                      Bucket=bucket,
                      Key=filename,
                      ContentType='multipart/form-data')
    imagespath="https://photogallery-vangmayi.s3.ap-south-1.amazonaws.com/"+filename
    img = ImageModel(path=imagespath, user_id=session["logged_in_user"], caption=des)
    img.save()
    print('image saved')
    return redirect(request.url)

def upload_media_to_twitter(access_token, access_token_secret):
    sampleimage = open("static/images/img.jpeg", "rb")
    media_params = {
        'media_category': 'tweet_image'
    }
    media_upload_url = "https://upload.twitter.com/1.1/media/upload.json"
    headeroauth = OAuth1(os.environ["TWT_CONSUMER_KEY"],
                         client_secret=os.environ["TWT_CONSUMER_SECRET"],
                         resource_owner_key=access_token,
                         resource_owner_secret=access_token_secret,
                         signature_type='auth_header')
    r = requests.post(media_upload_url, auth=headeroauth, params=media_params, files={'media': sampleimage})
    # after uploading the media its' media id is used to do a sucessful post to twitter
    if r.status_code == 200:
        result = r.json()
        status_params = {
            "media_ids": result['media_id'],
            "text": "sample tweet"
        }
        status_update_url = 'https://api.twitter.com/1.1/statuses/update.json'
        r = requests.post(status_update_url, auth=headeroauth, params=status_params)
        print(r)
        return True
    else:
        raise Exception(r)

@app.route('/', methods=["POST", "GET"])
@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        try:
            email = request.args.get('username')
            password = request.args.get('password')
            is_loggedin= login_func(email, password)
            if is_loggedin:
                return {
                    "action":"redirect",
                    "path":"/"
                }
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return {
                "action":"alert",
                "message":str(e)
                }
    elif request.method == "GET":
        if "logged_in_user" in session and session['logged_in_user']:
            return redirect('/upload')
        else:
            return render_template('front.html')

@app.route('/register',methods=["POST", "GET"])
def register():
    if request.method == "GET":
        if 'logged_in_user' in session and session['logged_in_user']:
            return redirect('/upload')
        else:
            return render_template('register.html')
    if request.method == 'POST':
        try:
            username = request.args.get('username')
            email = request.args.get('email')
            password = request.args.get('password')
            return register_func(username,email,password)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return "error"

@app.route('/upload',methods=["POST", "GET"])
def upload():
    if 'logged_in_user' in session and session['logged_in_user']:
        if request.method=="POST":
            des=request.form.get('des')
            if request.files:
                image=request.files['image']
                if image.filename=='':
                    return redirect(request.url)
                if not allowed_file(image.filename):
                    print("That type of file is not allowed")
                    return redirect(request.url)
                else:
                    filename = secure_filename(image.filename)
                    return upload_an_image(image,filename, des)
        images_list = ImageModel.fetchall(session["logged_in_user"])
        print(images_list)
        tagged_images_list=ImageModel.fetchtaggedimages(session["logged_in_user"])
        print(tagged_images_list)
        return render_template('upload.html', images_list=images_list, tagged_images_list=tagged_images_list, user_name=session["user_name"])
    else:
        return redirect('/')

@app.route('/tag',methods=["GET", "POST"])
def tag():
    if request.method=="POST":
        try:
            email=request.args.get("email")
            imageid=request.args.get("imageid")
            cursor.execute(f"select * from user where email='{email}'")
            data=cursor.fetchone()
            if data:
                cursor.execute(f"insert into taggedimages (user_id, image_id) values ({data['id']}, {imageid})")
                database.commit()
                return "True"
            else:
                return "False"
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return "error"
    elif request.method=="GET":
        return render_template("tagform.html")


@app.get('/oauth/twitter')
def get_access_token_and_post():
    try:
        authorization_pin = request.args.get("oauth_verifier")
        oauth_token=request.args.get("oauth_token")
        access_token, access_token_secret, user_id, screen_name=oauth_twitter.get_user_access_tokens(oauth_token, session['oauth_token_secret'], authorization_pin)
        session['oauth_token_secret']=None
        info=OauthModel(user_id=session["logged_in_user"],provider="twitter", access_token=access_token, access_token_secret=access_token_secret, expires_in=-1)
        info.save()
        #posting image to twitter after obtaining access token and secret
        result=upload_media_to_twitter(access_token, access_token_secret)
        if result==True:
            return "post successful"
        else:
            return "error occured"

    except Exception as e:
        print(e)
        traceback.print_exc()
        return {
            "action": "alert",
            "message": "error occured :" + str(e)
        }


@app.get('/oauth/fb')
def oauth_fb():
    code=request.args.get("code")
    params={
        "client_id":os.environ["FB_CLIENT_ID"],
        "redirect_uri":os.environ["DOMAIN"]+"/oauth/fb",
        "client_secret":os.environ["FB_CLIENT_SECRET"],
        "code":code
    }

    url="https://graph.facebook.com/v12.0/oauth/access_token"
    response=requests.get(url,params)
    return "True"


@app.route('/images/<imageid>/post-to-twitter',methods=["POST"])
def post_to_twitter(imageid=None):
    try:
        data=OauthModel.fetchaccesstoken(session['logged_in_user'], "twitter")
        if data and data.expires_in==-1:
            result = upload_media_to_twitter(data.access_token, data.access_token_secret)
            if result == True:
                return {
                "action":"alert",
                "message": "post successful"
            }
            else:
                return {
                "action":"alert",
                "message": "error occured"
            }

        # if access token got expired or wasn't evn present
        if(not data):
            oauth_token,oauth_token_secret=oauth_twitter.request_token()
            session['oauth_token_secret']=oauth_token_secret
            url = f"https://api.twitter.com/oauth/authorize?oauth_token={oauth_token}"

            return {
                "action":"redirect",
                "url":url
            }

    except Exception as e:
        print(e)
        traceback.print_exc()
        return {
            "action":"alert",
            "message": "error occured :"+ str(e)
        }

@app.route('/logout')
def logout():
    session['logged_in_user']=None
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
