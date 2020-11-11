''' A ToDo list Web App '''
from datetime import datetime
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required

app = Flask(__name__)
app.secret_key = "qwertyuiop"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)
    first_name = db.Column(db.String(50), nullable = False)
    last_name = db.Column(db.String(50), nullable = False)
    email = db.Column(db.String(100), nullable = False, unique = True)
    user_name = db.Column(db.String(100), nullable = False, unique = True)
    password = db.Column(db.String(1000), nullable = False)
    tasks = db.relationship("Todo", backref = "users", lazy = True)


class Todo(UserMixin, db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.String(200), nullable = False)
    date_created = db.Column(db.DateTime, default = datetime.now)
    task_completed = db.Column(db.Boolean, default = False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)


@app.route('/', methods = ["GET"])
def home():
    return render_template('home.html')

@app.route('/register/', methods = ["GET"])
def register():    
    return render_template('register.html')

@app.route('/register/', methods = ["POST"])
def register_post():
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    email = request.form["email"]
    user_name = request.form["user_name"]
    password = request.form["password"]

    user_with_unique_email = User.query.filter_by(email = email).first()
    user_with_unique_user_name = User.query.filter_by(user_name = user_name).first()

    # User with same email or user_name already exists
    if user_with_unique_email or user_with_unique_user_name:
        flash('User already exists! Try Logging in Instead!')
        return redirect(url_for('login'))

    new_user = User(first_name = first_name,
    last_name = last_name,
    email = email,
    user_name = user_name,
    password=generate_password_hash(password, method='sha256'))

    if new_user:
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration Successful!")
            return redirect(url_for("login"))
        except:
            return 'There was an issue. Try Again!'
    else:
        return redirect(url_for("login"))

@app.route('/login/', methods = ["GET"])
def login():
    return render_template("login.html")

@app.route('/login/', methods = ["POST"])
def login_post():
    user_name = request.form["name"]
    password = request.form["password"]
    # remember = True if request.form.get("remember") else False

    user = User.query.filter_by(user_name = user_name).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash("Please check your login details and try again.")
        return redirect(url_for("login")) # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user)
    # login_user(user, remember = remember)
    flash("Logged in Successfully! Welcome back :)")
    return redirect(url_for("to_do", user_name = user.user_name))


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully! We will miss you :(")
    return redirect(url_for("login"))

@app.route("/to_do/<string:user_name>/", methods = ["GET"])
@login_required
def to_do(user_name):
    user = User.query.filter_by(user_name = user_name).first()
    tasks = Todo.query.filter_by(user_id = user.id).order_by(Todo.date_created).all()
    return render_template("to_do.html", user_name = user_name, tasks = tasks)

@app.route("/to_do/<string:user_name>", methods = ["POST"])
@login_required
def to_do_post(user_name):
    user = User.query.filter_by(user_name = user_name).first()

    content = request.form.get("content")

    if content != "":
        try:
            task = Todo(user_id = user.id, content = content)
            db.session.add(task)
            db.session.commit()
        except:
            return "Error occured and the task couldn't be added!"
    else:
        return redirect(url_for("to_do", user_name = user.user_name))
    return redirect(url_for("to_do", user_name = user.user_name))

@app.route("/to_do/<string:user_name>/complete/<int:id>", methods = ["GET"])
@login_required
def task_incomplete(user_name,id):
    user = User.query.filter_by(user_name = user_name).first()
    incomplete_task = Todo.query.filter_by(user_id = user.id, id = id).first()
    incomplete_task.task_completed = True
    db.session.commit()
    tasks = Todo.query.filter_by(user_id = user.id).order_by(Todo.date_created).all()
    return render_template("to_do.html", user_name = user_name, tasks = tasks)

@app.route("/to_do/<string:user_name>/incomplete/<int:id>", methods = ["GET"])
@login_required
def task_complete(user_name,id):
    user = User.query.filter_by(user_name = user_name).first()
    complete_task = Todo.query.filter_by(user_id = user.id, id = id).first()
    complete_task.task_completed = False
    db.session.commit()
    tasks = Todo.query.filter_by(user_id = user.id).order_by(Todo.date_created).all()
    return render_template("to_do.html", user_name = user_name, tasks = tasks)

@app.route("/to_do/<string:user_name>/delete/<int:id>/", methods = ["GET"])
@login_required
def delete_task(user_name, id):
    user = User.query.filter_by(user_name = user_name).first()
    task_to_be_deleted = Todo.query.filter_by(id = id).first()
    try:
        db.session.delete(task_to_be_deleted)
        db.session.commit()
        return redirect(url_for("to_do", user_name = user.user_name))
    except:
        return "There was a problem in deleting that task!"

@app.route("/to_do/<string:user_name>/update/<int:id>", methods = ["GET"])
@login_required
def update(user_name, id):
    user = User.query.filter_by(user_name = user_name).first()
    task = Todo.query.filter_by(id = id).first()
    return render_template('update.html', task = task)

@app.route("/to_do/<string:user_name>/update/<int:id>", methods = ["POST"])
@login_required
def update_post(user_name, id):
    user = User.query.filter_by(user_name = user_name).first()
    task = Todo.query.get_or_404(id)
    task.content = request.form['content']

    try:
        db.session.commit()
        return redirect(url_for("to_do", user_name = user.user_name))
    except:
        return 'There was an issue updating your task'

if __name__ == '__main__':
    db.create_all()
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our users table, use it in the query for the user
        return User.query.get(int(user_id))
    app.run(debug=True)
