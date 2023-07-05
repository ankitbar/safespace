from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
from flask_sqlalchemy import SQLAlchemy
import boto3
import smtplib

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'your_secret_key'


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4'}
SENDER_EMAIL = 'ankit.baraskar1@gmail.com'

# Create a SQLite database connection
conn = sqlite3.connect('users.db',check_same_thread=False)
cursor = conn.cursor()

# Create a table to store user information
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')
conn.commit()

# AWS S3 configuration
S3_BUCKET = 'your_s3_bucket_name'
S3_REGION = 'your_aws_region'
s3 = boto3.client('s3', region_name=S3_REGION)

# SQLite database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    files = db.relationship('File', backref='user', lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_with = db.relationship('User', secondary='shared_files', lazy='subquery',
                                  backref=db.backref('shared_files', lazy=True))

    def __init__(self, filename, user_id):
        self.filename = filename
        self.user_id = user_id

shared_files = db.Table('shared_files',
    db.Column('file_id', db.Integer, db.ForeignKey('file.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

db.create_all()

# Helper functions
def send_email(receiver_email, subject, message,sender_email = SENDER_EMAIL):
    # Code to send email request to receiver_email
    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender_email, receiver_email, message)         
        print("Successfully sent email")
    except SMTPException:
        pass

def authenticate_file_access_request(requester, file_owner, file_name):
    receiver_email = file_owner.username  # Assume email address is the same as username
    subject = f'File Access Request: {file_name}'
    message = f'User {requester.username} is requesting access to your file: {file_name}. ' \
              f'Please approve or decline the request.'
    send_email(receiver_email, subject, message)

def get_user_files(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return user.files
    return []


@app.route('/')
def index():
    print(os.listdir('/'))
    return render_template('index.html')

@app.route('/upload/<username>', methods=['POST'])
def upload(username):
    file = request.files['file']
    if file and allowed_file(file.filename):
        # Generate a unique filename to avoid collisions
        filename = f'{username}_{file.filename}'
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Upload the file to S3
        s3.upload_fileobj(file, S3_BUCKET, file_path)

        # Create the file record in the database
        user = User.query.filter_by(username=username).first()
        file_record = File(filename=filename, user_id=user.id)
        db.session.add(file_record)
        db.session.commit()

        flash(f'File "{filename}" uploaded successfully.')
    else:
        flash('Invalid file type. Please upload an image, video, or PDF file.')

    return redirect(url_for('landing', username=username))

@app.route('/request_access/<username>/<file_id>', methods=['GET'])
def request_access(username, file_id):
    requester = User.query.filter_by(username=username).first()
    file = File.query.filter_by(id=file_id).first()
    if not requester or not file:
        flash('Invalid request.')
        return redirect(url_for('index'))

    if requester in file.shared_with:
        flash('Access already granted.')
    else:
        authenticate_file_access_request(requester, file.user, file.filename)
        flash('Access request sent to the file owner.')

    return redirect(url_for('landing', username=username))


@app.route('/files')
def files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('files.html', files=files)

@app.route('/download/<filename>')
def download(filename):
    # Check if the requested file belongs to the current user
    if filename in os.listdir(app.config['UPLOAD_FOLDER']):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        flash('You do not have permission to download this file.')
        return redirect(url_for('files'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Username already exists. Please choose a different username.')
        return redirect(url_for('index'))

    user = User(username=username, password=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()

    flash('Registration successful. Please log in.')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return redirect(url_for('landing', username=username))
    else:
        flash('Invalid username or password.')
        return redirect(url_for('index'))
    
@app.route('/landing/<username>', methods=['GET', 'POST'])
def landing(username):
    if request.method == 'POST':
        folder_name = request.form['folder_name']
        # Logic to create a new folder using folder_name
        flash(f'Folder "{folder_name}" created successfully.')

    files = get_user_files(username)
    folders = []  # Placeholder for folder retrieval logic

    return render_template('landing.html', username=username, files=files, folders=folders)



if __name__ == '__main__':
    app.run(debug=True)
