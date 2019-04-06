"""Accounts blueprint views"""
from flask import render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from app.core.models.user import User
from . import bp as app  # Note that app = blueprint, current_app = flask context
db = SQLAlchemy()


@app.route("/")
def home():
  return render_template('accounts/landing.html')


@app.route("/signin", methods=["GET", "POST"])
def signin():
  """Sign in
  """
  if request.method == "GET":
    return render_template("accounts/login.html")
  input_email = request.form["email"]
  input_password = request.form["password"]
  result = User.query.filter_by(email=input_email).first()
  if result is not None and result.VerifyPassword(input_password):
    session['uid'] = result.GetID()
    return redirect("/")
  error_msg = "User email or password is incorrect."
  return render_template("accounts/login.html", msg=error_msg)


@app.route("/signup", methods=["GET", "POST"])
def signup():
  """Sign up
  """
  if request.method == "GET":
    return render_template("accounts/signup.html")
  input_email = request.form["email"]
  input_password = request.form["password"]
  user = User(email=input_email, user_type=0)
  user.SetPassword(input_password)
  db.session.add(user)
  db.session.commit()
  return redirect("/")


@app.route("/signout")
def signout():
  """Sign out
  """
  del session['uid']
  return redirect("/")
