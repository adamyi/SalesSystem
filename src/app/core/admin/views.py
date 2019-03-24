"""Admin blueprint views"""

from . import bp as app  # Note that app = blueprint, current_app = flask context


@app.route("/")
def home():
  return "Admin Routes - hello world"
