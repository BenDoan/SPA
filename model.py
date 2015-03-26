from flask.ext.sqlalchemy import SQLAlchemy

class Model():
    def __init__(self, app):
        self.db = SQLAlchemy(app)
        db = self.db

        class User(self.db.Model):
            __tablename__ = 'users'

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

        class Course(self.db.Model):
            __tablename__ = 'courses'

            id = db.Column(db.Integer, primary_key=True)
            number = db.Column(db.Integer)
            title = db.Column(db.String)
            desc = db.Column(db.String)
            prereqs = db.Column(db.String)
            college = db.Column(db.String)

            def __init__(self, number="", title="", desc="", prereqs=""):
                self.number  = number
                self.title = title
                self.desc = desc
                self.prereqs = prereqs
        self.Course = Course

        class Requirement(self.db.Model):
            __tablename__ = 'requirements'

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String)
            credits = db.Column(db.Integer)

            def __init__(self, name, credits):
                self.name = name
                self.credits = credits
        self.Requirement = Requirement

        class ClassRequirement(self.db.Model):
            __tablename__ = 'class_requirements'
            id = db.Column(db.Integer, primary_key=True)

            requirement_id = db.Column(db.Integer, db.ForeignKey('requirements.id'))
            requirement = db.relationship('Requirement', backref=db.backref('ClassRequirement', lazy='dynamic'))

            course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
            course = db.relationship('Course', backref=db.backref('ClassRequirement', lazy='dynamic'))

            def __init__(self, requirement, course):
                self.requirement = requirement
                self.course = course
        self.ClassRequirement = ClassRequirement

        class UserHistory(self.db.Model):
            id = db.Column(db.Integer, primary_key=True)
            course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
            course = db.relationship('Course', backref=db.backref('UserHistory', lazy='dynamic'))

            def __init__(self, course):
                self.course = course
        self.UserHistory = UserHistory
