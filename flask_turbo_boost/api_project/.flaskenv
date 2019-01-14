# .flaskenv should be used for public variables, such as FLASK_APP,
# while .env should not be committed to your repository so that it can set private variables.

FLASK_APP=wsgi:app
FLASK_DEBUG=1
FLASK_RUN_PORT=5000

FLASK_SKIP_DOTENV=0
