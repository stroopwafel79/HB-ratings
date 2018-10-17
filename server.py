"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash,
                   session, url_for)

from model import User, Rating, Movie, connect_to_db, db
from flask_debugtoolbar import DebugToolbarExtension


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
    return render_template("homepage.html")


@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route("/users/<user_id>")
def show_user_page(user_id):
    """Show a user info page."""

    # get user info (age, zip) by user id
    curr_user = User.query.get(user_id)
    ratings = Rating.query.filter_by(user_id=user_id).all()


    return render_template("userpage.html", curr_user=curr_user, ratings=ratings)


@app.route("/login", methods=["GET"])
def show_login():

    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_user():

    new_email = request.form.get('email')
    pswd = request.form.get('password')
    # query db for an email that matches new_email.
    # return None if not found
    current_user = User.query.filter(User.email == new_email).first()
    # query db for password associated with new_email

    if current_user:
        if current_user.password == pswd:
            # add user if to Flask session
            session['user_id'] = current_user.user_id
            flash('Successfully logged in!')
            return redirect('/users/' + str(current_user.user_id))
        else:
            flash('Invalid password!')
    else:
        flash('User not found!')

    return redirect("/")


@app.route("/logout")
def log_out():
    """Logs user out of session."""

    session.clear()

    return redirect("/")


@app.route("/register", methods=["GET"])
def show_reg_form():
    """Displays a registration form and collects info from user."""

    return render_template("register_form.html")


@app.route("/register", methods=["POST"])
def process_reg():
    """Processes registration and adds user to DB."""
    new_email = request.form.get('email')
    pswd = request.form.get('password')
    db_email = User.query.filter(User.email == new_email).first()

    if not db_email:
        user = User(email=new_email,
                    password=pswd)
        db.session.add(user)
        db.session.commit()
        flash('New user successfully added!')
    else:
        flash('Email address already exists!')

    return redirect("/")


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
