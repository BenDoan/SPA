from flask.ext.sqlalchemy import SQLAlchemy

class Model():
    def __init__(self, app):
        self.db = SQLAlchemy(app)
        db = self.db

        class User(self.db.Model):
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True)
            email = db.Column(db.String(120), unique=True)
            password = db.Column(db.String)
            authenticated = db.Column(db.Boolean())
            is_admin = db.Column(db.Boolean())

            def __init__(self, username, email, is_admin=False):
                self.username = username
                self.email = email
                self.authenticated = False
                self.is_admin = is_admin

            def __str__(self):
                return "User: {}".format((self.id, self.username, self.email, self.password, self.authenticated, self.is_admin))

            def is_authenticated(self) :
                return self.authenticated

            def is_active(self) :
                return self.is_authenticated()

            def is_anonymous(self) :
                return False

            def get_id(self) :
                return self.username

        self.User = User
