from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
from flask_sqlalchemy import SQLAlchemy
import boto3

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'your_secret_key'


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4'}

# Example hardcoded user credentials - PROBABLY REDUNDANT
USERS = [
    {'username': 'user1', 'password': generate_password_hash('password1')},
    {'username': 'user2', 'password': generate_password_hash('password2')}
]

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

# THIS IS PROBABLY REDUNDANT
def get_user(username):
    for user in USERS:
        if user['username'] == username:
            return user
    return None

def verify_user(username, password):
    user = get_user(username)
    if user and check_password_hash(user['password'], password):
        return user
    return None

# END OF POSSIBLY REDUNDANT CODE

@app.route('/')
def index():
    print(os.listdir('/'))
    return render_template('index.html')

@app.route('/upload/<username>', methods=['GET', 'POST'])
def upload(username):
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            flash(f'File "{filename}" uploaded successfully.')
        else:
            flash('Invalid file type. Please upload an image, video, or PDF file.')

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hash the password before storing it in the database
        hashed_password = generate_password_hash(password)

        # Insert the user information into the database
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            flash('Registration successful. Please log in.')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose a different username.')

    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Retrieve the user from the database
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if user and check_password_hash(user[2], password):
        flash('Login successful.')
        # Additional logic after successful login
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

    # Logic to retrieve the user's files and folders
    files = get_user_files(username)
    folders = get_user_folders(username)

    return render_template('landing.html', username=username, files=files, folders=folders)



if __name__ == '__main__':
    app.run(debug=True)
