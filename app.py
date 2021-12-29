from pymongo import MongoClient
import jwt
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

@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
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
        time_token = (datetime.utcnow() + timedelta(seconds=30))
        header = {'id': id, 'exp': time_token}
        #python 버전에 따라 다르지만 현 버전에서는 decode 가 필요 없이 그냥 문자열임
        jwt_token = jwt.encode(header, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'time_token': jwt_token})
    else:
        return jsonify({'result': 'fail', 'msg':'아이디/비밀번호가 정확하지 않습니다.'})

@app.route('/sign_up')
def sign_up_page():
    #msg = request.args.get("msg")
    return render_template('sign_up.html')

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
        db.userinfo.insert_one({'id': username_receive, 'hash': password_receive, 'email':email_receive, 'gender':gender_receive})
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'fail'})
    # DB에 저장

@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    get_id = request.form['username_give']
    # ID 중복확인
    search_result = list(db.userinfo.find({'id': get_id}, {'_id':False}))
    if(len(search_result) != 0):#중z`복된 id가 존재한다.
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'fail'})

################################################################# instagram.html
@app.route('/instagram', methods=['GET'])
def user_get():
    # 이 자리에 DB에서 불러와야 함 user_doc =
    return jsonify({'list': userdoc})


@app.route('/instagram', methods=['POST'])
def user_post():
    title_receive = request.form['title_give']
    comment_receive = request.form['comment_give']
    user_doc = {
        'title': title_receive,
        'comment': comment_receive
    }
    print(user_doc) # 이 자리에 DB에 insert 해야함
    return jsonify({'msg': '포스팅이 완료되었습니다.'})

################################################################# comment.html(html명 아직 모름)
@app.route('/comment', methods=['GET'])
def user_get2():
    # 이 자리에 DB에서 불러와야 함 user_doc =
    return jsonify({'list': userdoc})


@app.route('/comment', methods=['POST'])
def user_post2():
    title_receive = request.form['title_give']
    comment_receive = request.form['comment_give']
    user_doc = {
        'title': title_receive,
        'comment': comment_receive
    }
    print(user_doc) # 이 자리에 DB에 insert 해야함
    return jsonify({'msg': '포스팅이 완료되었습니다.'})

# 한 db에서 보낼수 있나? 테스트할 필요성 있을듯


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)