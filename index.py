from models import *
from flask import Flask, render_template, redirect, request, session
from flask_session import Session
import traceback
from werkzeug.utils import secure_filename
import os
import boto3
import random


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
        # pics=dict(db.user.find_one(ObjectId(session['id'])))
        # tagpaths=[]
        # if "tagged" in pics.keys():
        #     tagged=pics["tagged"]
        #     for tag in tagged:
        #         image=db.uploads.find_one(ObjectId(tag))
        #         tagpaths.append(image['route'])
        #     print(tagpaths)
        return render_template('upload.html', images_list=images_list, tagged_images_list=tagged_images_list, user_name=session["user_name"])
    else:
        return redirect('/')

@app.route('/tag',methods=["GET", "POST"])
def tag():
    if request.method=="GET":
        imageid=request.args.get("imageid")
        return render_template("tagform.html", imageid=imageid)
    elif request.method=="POST":
        try:
            email=request.args.get("email")
            imageid=request.args.get("imageid")
            cursor.execute(f"select * from user where email='{email}'")
            data=cursor.fetchone()
            if data:
                cursor.execute(f"insert into taggedimages (user_id, image_id) values ({data['id']}, {imageid})")
                database.commit()
                return "Shared successfully"
            else:
                return "Enter email of valid user"
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return "error"

@app.route('/logout')
def logout():
    session['logged_in_user']=None
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
