from pymongo import MongoClient
import jwt, os
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

#client = MongoClient('내AWS아이피', 27017, username="아이디", password="비밀번호")
client = MongoClient('mongodb+srv://test:sparta@cluster0.mgxkf.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.dbinstaclone
#db.userinfo.insert_one({'id':'test', 'hash':'test'})
#client = MongoClient('mongodb+srv://test:sparta@cluster0.mgxkf.mongodb.net/Cluster0?retryWrites=true&w=majority')
#db = client.dbinstaclone

client_post_server = MongoClient('mongodb+srv://test:sparta@cluster0.i0lgb.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')
db_post = client_post_server.dbpost
db_imgs = client_post_server.dbimg
#db_post.postinfo.insert_one({'writer':'test@gmail.com', 'like':0, 'img':'', 'comment':''})

@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload['id'])
        return render_template('index.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    id = request.form['username_give']#이메일받아오는거임 아이디아님
    hassed_pw = request.form['password_give']
    search_result = list(db.userinfo.find({'$and': [{'email': id}, {'hash': hassed_pw}]}, {'_id':False}))
    # 로그인
    if(len(search_result)==1):
        time_token = (datetime.utcnow() + timedelta(seconds=300))
        header = {'id': id, 'exp': time_token}
        #python 버전에 따라 다르지만 현 버전에서는 decode 가 필요 없이 그냥 문자열임
        jwt_token = jwt.encode(header, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'time_token': jwt_token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 정확하지 않습니다.'})

@app.route('/sign_up')
def sign_up_page():
    #msg = request.args.get("msg")
    return render_template('sign_up.html')

@app.route('/user')
def user_page():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        #print(payload['id'])
        return render_template('user.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/user/give_user_page', methods=['POST'])
def post_user_page():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        userinfo_find = list(db.userinfo.find({"email":payload['id']}))
        profile_pic_name = userinfo_find[0]['profile_img']
        user_id = userinfo_find[0]['id']
        follower = list(db.userinfo.find({"email":payload['id']}))[0]['follower']
        follow = list(db.userinfo.find({"email": payload['id']}))[0]['follow']
        post = list(db_post.postinfo.find({"email":payload['id']}, {'_id': False}))
        print(profile_pic_name)
        data = {
            'user_id' : user_id,
            'profile_pic_name' :  profile_pic_name,
            'post_num' : len(post),
            'follower' : follower,
            'follow' : follow,
            'posts_list' :post
        }
        return jsonify({'result': data})
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    # 회원가입
    username_receive = request.form['username_give']#유저의 닉네임
    password_receive = request.form['password_give']
    email_receive = request.form['email_give']#유저의 이메일
    gender_receive = request.form['gender_give']
    #아래는 해쉬되어서 온다는 가정
    search_result = list(db.userinfo.find({'$or': [{'email': email_receive}, {'id':username_receive}]}, {'_id': False}))
    if(len(search_result) == 0):
        db.userinfo.insert_one({
            'id': username_receive,
            'hash': password_receive,
            'email':email_receive,
            'gender':gender_receive,
            'follower':{},
            'follow':{},
            'profile_img':False
        })
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'fail'})
    # DB에 저장

@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    get_id = request.form['username_give']
    # ID 중복확인
    search_result = list(db.userinfo.find({'email': get_id}, {'_id':False}))
    if(len(search_result) != 0):#중z`복된 id가 존재한다.
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'fail'})

@app.route('/fileupload', methods=['POST'])
def file_upload():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # title_receive = request.form['title_give']#이미지 저장시 이미지 제목 받음(이미지 파일이름아님)
        file = request.files['file_give']  # 이미지 파일 받음
        title_receive = file.filename.split('.')[0]  # 이미지 파일 제목
        extension = file.filename.split('.')[-1]  # 이미지 확장자
        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

        comment = request['comment']

        filename = f'{title_receive}-{mytime}'  # 이미지파일이름-시간
        # static/user_img/ 에 요청 이미지파일이름-시간.확장자 형태로 저장된다.
        save_to = f'static/user_img/{filename}.{extension}'
        file.save(save_to)

        doc = {'title': title_receive, 'img': f'{filename}.{extension}'}
        db_imgs.img.insert_one(doc)
        doc_for_post = {
            'img': f'{filename}.{extension}',
            'id': payload['id'],
            'like':0,
            'comment':comment
        }
        db_post.postinfo.insert_one()
        # db_post.postinfo.insert_one({'writer':'test@gmail.com', 'like':0, 'img':'', 'comment':''})
        # doc = {'title': title_receive, 'img': f'{filename}.{extension}'}
        # db.camp.insert_one(doc)
        return jsonify({'result': 'success'})
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/user/fileupload', methods=['POST'])
def user_file_upload():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # title_receive = request.form['title_give']#이미지 저장시 이미지 제목 받음(이미지 파일이름아님)
        file = request.files['file_give']  # 이미지 파일 받음
        title_receive = file.filename.split('.')[0]  # 이미지 파일 제목
        extension = file.filename.split('.')[-1]  # 이미지 확장자
        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

        filename = f'{title_receive}-{mytime}'  # 이미지파일이름-시간
        save_file_name =f'{filename}.{extension}'
        # static/user_img/ 에 요청 이미지파일이름-시간.확장자 형태로 저장된다.
        save_to = f'static/user_img/{filename}.{extension}'
        save_to = f'\\static\\user_img\\{filename}.{extension}'
        print(save_to)
        print(file)
        #file.save(save_to)
        cur_path = os.getcwd()+save_to
        print(cur_path)
        #app.config['UPLOAD_FOLDER'] = os.getcwd()+'\'
        #f.save(os.path.join(app.config['UPLOAD_FOLDER'], 'tmp.png'))
        file.save(cur_path)
        doc = {'title': title_receive, 'img': f'{filename}.{extension}'}
        db_imgs.img.insert_one(doc)
        #######여기 위까지가 이미지 저장
        #바로아랫줄은 유저 프로필사진 업데이트
        db.userinfo.update_one({"email":payload['id']}, {"$set":{'profile_img':save_file_name}})
        return jsonify({'result': 'success'})
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)