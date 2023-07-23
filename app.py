import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure user loader function, User model, and LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

PATH_TO_USER_FILES = 'data'
SHARED_PATH = 'shared'
class User:
    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def get_id(self):
        return self.username

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

@login_manager.user_loader
def load_user(username):
    # Implement your logic to load the user from a database or other data source
    # Example:
    if username == 'user1':
        return User(username='user1', password='password1')
    elif username == 'user2':
        return User(username='user2', password='password2')
    return None

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class CreateFolderForm(FlaskForm):
    folder_name = StringField('Folder Name', validators=[DataRequired()])
    submit = SubmitField('Create Folder')

class CreateSharedFolderForm(FlaskForm):
    shared_folder_name = StringField('Folder Name', validators=[DataRequired()])
    shared_with_email = StringField('Share with Email', validators=[DataRequired()])
    submit = SubmitField('Create Shared Folder')

@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = load_user(username)
        if user and user.verify_password(password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html', form=form)

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    create_folder_form = CreateFolderForm()
    create_shared_folder_form = CreateSharedFolderForm()

    if create_folder_form.validate_on_submit():
        folder_name = create_folder_form.folder_name.data
        # Logic to create a new folder specific to the user
        flash(f'Folder "{folder_name}" created successfully.')

    if create_shared_folder_form.validate_on_submit():
        shared_folder_name = create_shared_folder_form.shared_folder_name.data
        shared_with_email = create_shared_folder_form.shared_with_email.data
        # Logic to create a new shared folder and send notification to the specified email
        flash(f'Shared folder "{shared_folder_name}" created and shared with {shared_with_email}.')

    # Retrieve the list of files and folders accessible to the current user
    user_file_path = os.path.join(PATH_TO_USER_FILES, current_user.username)

    if not(os.path.exists(user_file_path)):
        os.makedirs(user_file_path)

    files_and_folders = os.listdir(user_file_path)
    files = [f for f in files_and_folders if os.path.isfile(os.path.join(user_file_path, f))]
    folders = [f for f in files_and_folders if os.path.isdir(os.path.join(user_file_path, f))]

    return render_template('home.html',
                           create_folder_form=create_folder_form,
                           create_shared_folder_form=create_shared_folder_form,
                           folders=folders,files = files)

@app.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    folder_name = request.form['folder_name']
    folder_path = os.path.join(PATH_TO_USER_FILES, current_user.username, folder_name)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        flash(f'Folder "{folder_name}" created successfully.')
    else:
        flash(f'Folder "{folder_name}" already exists.')

    return redirect(url_for('home'))

@app.route('/create_shared_folder', methods=['POST'])
@login_required
def create_shared_folder():
    shared_folder_name = request.form['shared_folder_name']
    shared_with_email = request.form['shared_with_email']
    folder_path = os.path.join(SHARED_PATH, current_user.username, shared_folder_name)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        flash(f'Shared folder "{shared_folder_name}" created and shared with {shared_with_email}.')
        # Logic to send email notification to shared_with_email
    else:
        flash(f'Folder "{shared_folder_name}" already exists.')

    return redirect(url_for('home'))


@app.route('/view_folder/<folder_name>', methods=['GET'])
@login_required
def view_folder(folder_name):
    user_file_path = os.path.join('path_to_user_files', current_user.username, folder_name)
    files_and_folders = os.listdir(user_file_path)
    files = [f for f in files_and_folders if os.path.isfile(os.path.join(user_file_path, f))]
    folders = [f for f in files_and_folders if os.path.isdir(os.path.join(user_file_path, f))]
    return render_template('folder_view.html', folder_name=folder_name, folders=folders, files=files)

@app.route('/view_file/<file_name>', methods=['GET'])
@login_required
def view_file(file_name):
    file_path = os.path.join('path_to_user_files', current_user.username, file_name)
    # You can customize how you want to display the file content
    # For example, for text files, you can read the content and pass it to the template
    # For images and videos, you can use appropriate HTML elements to render them in the template
    return render_template('file_view.html', file_name=file_name)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)