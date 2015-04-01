from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.schema import UniqueConstraint

class Model():
    def __init__(self, app):
        self.db = SQLAlchemy(app)
        db = self.db

        class User(self.db.Model):
            __tablename__ = 'users'

            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True)
            email = db.Column(db.String(120))
            password = db.Column(db.String)
            authenticated = db.Column(db.Boolean())

            def __init__(self, username, email):
                self.username = username
                self.email = email
                self.authenticated = False

            def __str__(self):
                return "User: {}".format((self.id, self.username, self.email, self.password, self.authenticated))

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
            __table_args__ = (UniqueConstraint('college', 'number'),)

            id = db.Column(db.Integer, primary_key=True)
            number = db.Column(db.Integer, nullable=False)
            title = db.Column(db.String, nullable=False)
            desc = db.Column(db.String, nullable=False)
            prereqs = db.Column(db.String)
            college = db.Column(db.String, nullable=False)

            def __init__(self, number="", title="", desc="", prereqs=""):
                self.number  = number
                self.title = title
                self.desc = desc
                self.prereqs = prereqs

            def __getitem__(self, compare):#dirty hack to make sorting work...
                if compare == 'number':
                     return self.number
                elif compare == 'college':
                     return self.college

        self.Course = Course

        class Requirement(self.db.Model):
            __tablename__ = 'requirements'
            __table_args__ = (UniqueConstraint('major', 'name'),)

            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String)
            major = db.Column(db.String, nullable=False)
            credits = db.Column(db.Integer, nullable=False)

            def __init__(self, name, major, credits):
                self.name = name
                self.major = major
                self.credits = credits
        self.Requirement = Requirement

        class CourseRequirement(self.db.Model):
            __tablename__ = 'class_requirements'
            id = db.Column(db.Integer, primary_key=True)

            requirement_id = db.Column(db.Integer, db.ForeignKey('requirements.id'), nullable=False)
            requirement = db.relationship('Requirement', backref=db.backref('CourseRequirement', lazy='dynamic'))

            course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
            course = db.relationship('Course', backref=db.backref('CourseRequirement', lazy='dynamic'))

            def __init__(self, requirement, course):
                self.requirement = requirement
                self.course = course
        self.CourseRequirement = CourseRequirement

        class UserHistory(self.db.Model):
            id = db.Column(db.Integer, primary_key=True)
            course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
            course = db.relationship('Course', backref=db.backref('UserHistory', lazy='dynamic'))

            def __init__(self, course):
                self.course = course
        self.UserHistory = UserHistory
