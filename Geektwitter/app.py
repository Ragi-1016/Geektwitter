from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required,current_user
import os
import pytz
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import hashlib



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SECRET_KEY"] = os.urandom(24)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


class Post(db.Model):
     id = db.Column(
         db.Integer, primary_key=True
     )  # primary_key : それぞれの投稿を判断する主Key
     title = db.Column(db.String(50), nullable=False)
     body = db.Column(db.String(400), nullable=False)
     created_at = db.Column(
         db.DateTime, nullable=False, default=datetime.now(pytz.timezone("Asia/Tokyo"))
     )

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))
    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def top():
    return render_template("login.html")

@app.route("/index", methods=["GET", "POST"])
@login_required
def index():
     if request.method == "POST":
         text_input = request.form.get("search")
         print(f"text_input : {text_input}")
         if (text_input is None) or len(text_input) == 0:
             posts = Post.query.order_by(Post.created_at.desc()).all()
         else:
             posts = (
                 db.session.query(Post)
                 .filter(
                     or_(
                         Post.body.contains(text_input),
                         Post.title.contains(text_input),
                     )
                 )
                 .all()
             )
         return render_template("index.html", posts=posts)
     else:
         posts = Post.query.all()
         return render_template("index.html", posts=posts)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form.get("password")

        # ユーザー名の存在チェック
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("そのユーザー名は既に登録されています。別のユーザー名をご登録ください。", "error")
            return render_template("signup.html")

        # ユーザーの作成と保存
        try:
            user = User(
                username=username,
                password=generate_password_hash(password, method="sha256"),
             )  # インスタンス化
            db.session.add(user)
            db.session.commit()
            return redirect("/login")
        except IntegrityError:
            db.session.rollback()
            return render_template("signup.html")

    return render_template("signup.html")




@app.route("/login", methods=["GET", "POST"])
def login():
     if request.method == "POST":
         try:
             username = request.form["username"]
             password = request.form.get("password")
 
             # usernameでフィルターをかけて合致したものを持ってくる
             user = User.query.filter_by(username=username).first()
             if check_password_hash(user.password, password):
                 login_user(user)
                 return redirect("/index")
             else:
                 texts = [
                     "パスワードが異なります！",
                     "パスワードを忘れた場合はアカウントを作成しなおしてください",
                 ]
                 return render_template("login.html", texts=texts)
         except:
             texts = [
                 "ユーザー名が異なります！",
                 "未登録の場合はアカウントを作成してください",
             ]
             return render_template("login.html", texts=texts)
     else:
         return render_template("login.html")

@app.route("/logout")
@login_required  # loginしているユーザーしかアクセスできない
def logout():
     logout_user()
     return redirect("/login")
          
@app.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        # POSTメソッドの時の処理。
        title = request.form.get("title")
        body = request.form.get("body")
        post = Post(title=title, body=body)
        # DBに値を送り保存する
        post = Post(title=title, body=body)
        db.session.add(post)
        db.session.commit()
        return redirect("/index")
    else:
        # GETメソッドの時の処理
        return render_template("new.html")


@app.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def update(id):
    post = Post.query.get(id)
    if request.method == "GET":
        return render_template("edit.html", post=post)
    else:
        post.title = request.form.get("title")
        post.body = request.form.get("body")
        db.session.commit()
        return redirect("/index")


@app.route("/<int:id>/delete", methods=["GET"])
@login_required
def delete(id):
    post = Post.query.get(id)
    # 投稿を削除
    db.session.delete(post)
    # 削除を反映
    db.session.commit()
    return redirect("/index")

if __name__ == "__main__":
    app.run(debug=True)
