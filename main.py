from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from hashutils import make_hash, check_hash
import re

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:MyNewPass@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner, pub_date=None):
        self.title = title
        self.body = body
        self.owner = owner
        if pub_date is None:
            pub_date = datetime.now()
        self.pub_date = pub_date

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(120), nullable=False) # potential problem with hash length
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password_hash = make_hash(password)

endpoints_with_login = ['newpost']

@app.before_request
def require_login():
    if request.endpoint in endpoints_with_login and not isLoggedIn():
        return redirect('/login')

def isLoggedIn():
    return 'username' in session

def getUser():
    if isLoggedIn():
        return session['username']
    return ''

@app.route('/login', methods=['POST', 'GET'])
def login():
    username = ''
    username_error = ''
    password_error = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if username:
            if user:
                if password:
                    if len(make_hash(password)) != len(user.password_hash):
                        flash('uh-oh', 'error')
                    elif check_hash(password, user.password_hash):
                        session['username'] = username
                        return redirect('/blog/newpost')
                    else:
                        password_error = 'User password incorrect'
                else:
                    password_error = 'Please enter your password'
            else:
                username_error = 'No user exists'
        else:
            username_error = 'Please enter a username'

    return render_template('login.html', title='Blogz', username=username, username_error=username_error, password_error=password_error, isLoggedIn=isLoggedIn())

username_pattern = re.compile('^(?=\S{4,20}$)')

# no spaces
# min length is 4 and max length is 20
def isValidUsername(username):
    if ' ' in username:
        return False
    return re.search(username_pattern, username)

password_pattern = re.compile('^(?=\S{6,40}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[^A-Za-z\s0-9])')

# no spaces
# min length is 6 and max length is 40
# at least include a digit number
# at least an uppercase and a lowercase letter
# at least a special character
def isValidPassword(password):
    if ' ' in password:
        return False
    return re.search(password_pattern, password)

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    username = ''
    username_error = ''
    password_error = ''
    verify_error = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            username_error = 'Sorry, username already taken'
        else:
            if username:
                if isValidUsername(username):
                    if password:
                        if isValidPassword(password):
                            if verify:
                                if verify == password:
                                    new_user = User(username, password)
                                    db.session.add(new_user)
                                    db.session.commit()
                                    session['username'] = username
                                    return redirect('/blog/newpost')
                                else:
                                    verify_error = 'Passwords do not match'
                            else:
                                verify_error = 'Nothing to verify'
                        else:
                            password_error = 'Password not valid'
                    else:
                        password_error = 'Please enter a password'
                else:
                    username_error = 'Username not valid'
            else:
                username_error = 'Please enter a username'

    return render_template('signup.html', title='Blogz', username=username, username_error=username_error, password_error=password_error, verify_error=verify_error, current_user=getUser(), isLoggedIn=isLoggedIn())

@app.route('/logout')
def logout():
    if isLoggedIn():
        del session['username']
    return redirect('/blog')

@app.route('/blog/newpost', methods=['POST', 'GET'])
def newpost():
    if request.method == 'POST':
        owner = User.query.filter_by(username=session['username']).first()
        blog_title = request.form['title']
        blog_body = request.form['body']
        new_blog = Blog(blog_title, blog_body, owner)
        db.session.add(new_blog)
        db.session.commit()
        return redirect('/blog')

    return render_template('newpost.html', title='Blogz', current_user=getUser(), isLoggedIn=isLoggedIn())

@app.route('/blog', methods=['POST', 'GET'])
def blogs():
    id = request.args.get('id')
    username = request.args.get('user')

    if id:
        blog = Blog.query.get(id)
        return render_template('blogs.html', title='Blogz', blog=blog, current_user=getUser(), isLoggedIn=isLoggedIn())

    if username:
        blogs = User.query.filter_by(username=username).first().blogs
        return render_template('singleUser.html', title='Blogz', blogs=blogs, username=username, postnew=request.method == 'POST', current_user=getUser(), isLoggedIn=isLoggedIn())

    blogs = Blog.query.order_by(Blog.pub_date.desc()).all()
    return render_template('blogs.html', title="Build a Blog!", blogs=blogs, current_user=getUser(), isLoggedIn=isLoggedIn())

@app.route('/', methods=['POST', 'GET'])
def index():
    users = User.query.all()
    return render_template('index.html', title='Blogz', users=users, current_user=getUser(), isLoggedIn=isLoggedIn())

if __name__ == '__main__':
    app.run()