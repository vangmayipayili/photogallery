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
        return "True"
    else:
        return "False"
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


@app.route('/', methods=["POST", "GET"])
@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        try:
            email = request.args.get('username')
            password = request.args.get('password')
            return login_func(email, password)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return "error"
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
def oauth_twitter():
    code = request.args.get("code")
    # for authorization(like client secret)
    auth_string = f'{os.environ["TWT_CLIENT_ID"]}:{os.environ["TWT_CLIENT_SECRET"]}'
    sample_string_bytes = auth_string.encode("ascii")
    base64_bytes = base64.b64encode(sample_string_bytes)
    base64_string = base64_bytes.decode("ascii")
    headers={
        "Authorization":'Basic '+ base64_string
    }
    params = {
        "client_id": os.environ["TWT_CLIENT_ID"],
        "redirect_uri": os.environ["DOMAIN"] + "/oauth/twitter",
        # "client_secret": os.environ["TWT_CLIENT_SECRET"],
        "code": code,
        'grant_type':'authorization_code',
        'code_verifier':'challenge'
    }

    url = "https://api.twitter.com/2/oauth2/token"
    current_time = datetime.now()
    response = requests.post(url, params, headers=headers)
    response_data=response.json()
    if response.status_code != 200:
        return {
            "error": response_data
        }
    access_token=response_data.get("access_token")
    provider = "twitter"

    expires_in_seconds=response_data.get("expires_in",0)
    expires_in_date=current_time+timedelta(seconds=expires_in_seconds)
    # to epoch time
    expires_in=datetime.timestamp(expires_in_date)
    info=OauthModel(user_id=session["logged_in_user"],provider=provider, access_token=access_token, expires_in=expires_in)
    info.save()
    return "True"

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
        current_date = datetime.now()
        epoch_time=0
        expires_in = datetime.fromtimestamp(epoch_time)
        data=OauthModel.fetchaccesstoken(session['logged_in_user'], "twitter")
        if data:
            epoch_time=data.expires_in
            expires_in=datetime.fromtimestamp( epoch_time )
            if(expires_in>current_date):
                sampleimage = open("static/images/img.jpeg", "rb").read()
                headers={
                    'Authorization': "Bearer "+ data.access_token,
                    'Content-Type':'application/x-www-form-urlencoded'
                }
                params={
                    "media": sampleimage,
                    'media_category':'tweet_image'
                }
                url="https://upload.twitter.com/1.1/media/upload.json"
                response = requests.post(url, headers=headers, params= params)
                response_data=response.json()
                return {
                    "action":"alert",
                    "message": "Hi "+response_data['data']['name']
                }

        if(not data or expires_in<current_date):
            params={
                "response_type": "code",
                "client_id":os.environ["TWT_CLIENT_ID"],
                "redirect_uri":os.environ["DOMAIN"]+"/oauth/twitter",
                "scope":"tweet.read users.read offline.access",
                "code_challenge_method": "plain",
                "code_challenge":"challenge",
                "state" : "state"
            }
            url="https://twitter.com/i/oauth2/authorize?"+urllib.parse.urlencode(params)
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
