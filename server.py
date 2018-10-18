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


# @app.route("/login", methods=["GET"])
# def show_login():

#     return render_template("login.html")


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


@app.route("/movies")
def show_movies():
    """ Show a list of movies """
    movies = Movie.query.order_by(Movie.title).all()

    return render_template("movie_list.html", movies=movies)


@app.route("/movies/<movie_id>")
def show_movie_details(movie_id):
    """ Show all ratings of a given movie"""

    BERATEMENT_MESSAGES = [
        "I suppose you don't have such bad taste after all.",
        "I regret every decision that I've ever made that has " +
        "brought me to listen to your opinion.",
        "Words fail me, as your taste in movies has clearly " +
        "failed you.",
        "That movie is great. For a clown to watch. Idiot.",
        "Words cannot express the awfulness of your taste."
    ]

    movie = Movie.query.get(movie_id)
    # ratings = Rating.query.filter_by(movie_id=movie_id).all()

    user_id = session.get("user_id")

    if user_id:
        user_rating = Rating.query.filter_by(
            movie_id=movie_id, user_id=user_id).first()

    else:
        user_rating = None

    # Get average rating of movie

    rating_scores = [r.score for r in movie.ratings]
    avg_rating = float(sum(rating_scores)) / len(rating_scores)

    prediction = None

    # Prediction code: only predict if the user hasn't rated it.

    if (not user_rating) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)

    # Either use the prediction or their real rating

    if prediction:
        # User hasn't scored; use our prediction if we made one
        effective_rating = prediction

    elif user_rating:
        # User has already scored for real; use that
        effective_rating = user_rating.score

    else:
        # User hasn't scored, and we couldn't get a prediction
        effective_rating = None

    # Get the eye's rating, either by predicting or using real rating

    the_eye = User.query.filter_by(email="the-eye@of-judgement.com").one()
    eye_rating = Rating.query.filter_by(
        user_id=the_eye.user_id, movie_id=movie.movie_id).first()

    if eye_rating is None:
        eye_rating = the_eye.predict_rating(movie)

    else:
        eye_rating = eye_rating.score

    if eye_rating and effective_rating:
        difference = abs(eye_rating - effective_rating)

    else:
        # We couldn't get an eye rating, so we'll skip difference
        difference = None

    if difference:
        beratement = BERATEMENT_MESSAGES[int(difference)]

    else:
        beratement = None

    return render_template(
        "movie_details.html",
        movie=movie,
        user_rating=user_rating,
        average=avg_rating,
        prediction=prediction,
        beratement=beratement
        )

@app.route("/rate", methods=["POST"])
def add_rating():
    """Adds user rating for film to DB."""

    user_rating = request.form.get('add_rating')
    movie_id = request.form.get('movie_id')
    db_rating = Rating.query.filter((Rating.user_id == session['user_id']) &
                                    (Rating.movie_id == movie_id)).first()

    if not db_rating:
        rating = Rating(movie_id=movie_id,
                        score=user_rating,
                        user_id=session['user_id'])
        db.session.add(rating)
        db.session.commit()
        flash('Rating successfully added!')
    else:
        db_rating.score = user_rating
        db.session.commit()
        flash('Rating updated!')

    return redirect('/movies/' + str(movie_id))

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
