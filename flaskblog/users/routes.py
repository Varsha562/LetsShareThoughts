from flask import render_template,url_for,flash,redirect,request,Blueprint
from flask_login import login_user,current_user,logout_user,login_required
from flaskblog import db,bcrypt
from flaskblog.model import User,Post
from flaskblog.users.forms import ResetPassword,RegistrationForm,LoginForm,UpdateForm,RequestResetForm
from flaskblog.users.utils import save_picture,send_reset_email

users = Blueprint('users',__name__)

@users.route("/register", methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
       return redirect(url_for('main.home'))
    form=RegistrationForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user=User(username=form.username.data,email=form.email.data,password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!','success')
        return redirect(url_for('users.login'))
    return render_template('register.html' , title='Register' , form=form)

@users.route("/login" , methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
       return redirect(url_for('main.home'))
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user,remember=form.remember.data)
            flash('You have been logged in!','success')
            next_page=request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login unsuccessful.Please check username and password','danger')
    return render_template('login.html' , title='Login' , form=form)

@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@users.route("/account" , methods=['POST','GET'])
@login_required
def account():
    form=UpdateForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file=save_picture(form.picture.data)
            current_user.image_file=picture_file
        current_user.username=form.username.data
        current_user.email=form.email.data
        db.session.commit()
        flash('Your account has been Updated!','success')
        return redirect(url_for('users.account'))
    elif request.method=='GET':
        form.username.data=current_user.username
        form.email.data=current_user.email
    image_file=url_for('static',filename='profile_pics/' + current_user.image_file )
    return render_template('account.html' , title='Account', image_file=image_file , form=form)

@users.route("/user/<string:username>")
def user_posts(username):
    page=request.args.get('page',1,type=int)
    user=User.query.filter_by(username=username).first_or_404()
    posts=Post.query.filter_by(author=user)\
          .order_by(Post.date_posted.desc())\
          .paginate(page=page,per_page=5)
    return render_template('user_posts.html',post=posts,user=user)

@users.route("/reset_password" , methods=['GET','POST'])
def request_reset():
    if current_user.is_authenticated:
       return redirect(url_for('main.home'))
    form=RequestResetForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('A reset password message has been sent on your E-mail.Please follow the instructions','info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html' , title='Reset Password' , form=form)

@users.route("/reset_password/<token>" , methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
       return redirect(url_for('main.home'))
    user=User.query.get(token)
    if user is None:
        flash('This token is invalid or expired!', 'warning')
        return redirect(url_for('users.reset_request'))
    form=ResetPassword()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password=hashed_password
        db.session.commit()
        flash(f'Account updated for {form.username.data}!', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html' , title='Reset Password' , form=form)

