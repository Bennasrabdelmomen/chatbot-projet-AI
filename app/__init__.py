from flask import Flask

def create_app():
    """
    Create and configure the Flask app.
    """
    app = Flask(__name__)
    return app
