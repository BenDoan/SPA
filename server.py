from flask import *

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask.ext.assets import Environment, Bundle
from htmlmin import minify
from flask.ext.login import LoginManager,login_user,logout_user, current_user, login_required
from flask_wtf import Form
from wtforms import StringField, PasswordField, TextField, TextAreaField
from wtforms.validators import DataRequired
from passlib.hash import pbkdf2_sha256
from operator import itemgetter

import random
import logging
import collections

from model import Model
from requirements import ScheduledCourse

app = Flask(__name__)
loginmanager = LoginManager()
loginmanager.init_app(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/spa.db'

app.config['DEBUG'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

LOG_FORMAT = '%(asctime)s|%(levelname)s|%(message)s'
logging.basicConfig(format=LOG_FORMAT)

assets = Environment(app)
assets.url_expire = False

css = Bundle('css/main.css', 'css/bootstrap.css', 'css/bootstrap-theme.css', filters="cssmin", output='css/gen/packed.css')
assets.register('css_all', css)

model = Model(app)
db = model.db


## Authentication
class LoginForm(Form):
    name = StringField('name', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])

class SignupForm(Form):
    name = StringField('name', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    repeatpassword = PasswordField('repeatpassword', validators=[DataRequired()])

class AddRoomForm(Form):
    title = TextField('title', validators=[DataRequired()])
    number = TextField('number', validators=[DataRequired()])
    short_description = TextAreaField('short_description', validators=[DataRequired()])
    long_description = TextAreaField('long_description', validators=[DataRequired()])
    image = TextField('image', validators=[DataRequired()])

def create_user(username, email, password):
    newuser = model.User(username,email)
    newuser.password = pbkdf2_sha256.encrypt(password)
    db.session.add(newuser)
    db.session.commit()
    return newuser

@loginmanager.user_loader
def load_user(userid):
    users =  model.User.query.filter_by(username=userid)
    return users.first()

@app.route('/authenticate', methods=['GET','POST'])
def authenticate():
    form = LoginForm()
    if form.validate_on_submit():
        users = model.User.query.filter_by(username=request.form["name"])
        user = users.first()
        if user != None :
            if pbkdf2_sha256.verify(request.form["password"], user.password) :
                user.authenticated = True
                db.session.commit()
                login_user(user)
    return redirect(request.form["redirect"])

@app.route('/signin', methods=['GET','POST'])
def login():
    form = LoginForm()
    if request.method == 'GET' :
        return render_template("signin.html",form = form,error = "")
    error = "some fields were empty"
    if form.validate_on_submit():
        users = model.User.query.filter_by(username = request.form["name"])
        user = users.first()
        if user != None :
            if pbkdf2_sha256.verify(request.form["password"],user.password) :
                user.authenticated = True
                db.session.commit()
                login_user(user)
                return redirect("/")
        error = "incorrect username or password"
    return render_template("signin.html",form = form,error = error);

@app.route('/signup', methods=['GET','POST'])
def signup():
    form = SignupForm()
    if request.method == 'GET' :
        return render_template("signup.html",form = form,error="")
    error = "some fields were empty"
    if form.validate_on_submit():
        error = "some fields were empty"
        if request.form["password"] == request.form["repeatpassword"]:
            user = create_user(request.form["name"], request.form["email"], request.form["password"])
            user.authenticated = True
            db.session.commit()
            login_user(user)
            return redirect("/")
        else:
            error = "passwords did not match"
    return render_template("signup.html",form = form,error=error)

@login_required
@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(request.args.get("redirect"))

@app.route('/getuser', methods=['GET'])
def getuser():
    admin = model.User.query.filter_by(username='admin').first()
    return admin.username

@login_required
@app.route('/signout')
def signout():
    logout_user()
    return redirect('/signin')

##Content
@login_required
@app.route('/', methods=['GET'])
def index():
    if current_user.is_anonymous():
        return redirect("/signin")
    return render_template('index.html')

@login_required
@app.route('/profile', methods=['GET'])
def profile():
    return render_template('profile.html')

@login_required
@app.route('/classSelector',methods=['GET'])
def class_selector():
    selectedMajor = request.args.get('majorSelected', 'None')

    courses=get_courses_for_major(selectedMajor)

    #Sorting the colleges so that we dont have multiple different ones from requirements
    sortedColleges = sorted(courses, key=itemgetter('college'))
    sortedCourses=[]
    sortCollege=[]
    prevCollege=""
    for course in sortedColleges:
        if course.college == prevCollege:#same college, just add and go
            sortCollege.append(course)
        elif prevCollege != "":#not equal and not the starting value
            y = sorted(sortCollege, key=itemgetter('number'))
            for x in y:
                sortedCourses.append(x)
            sortCollege=[course]
            prevCollege=course.college
        else:#starting value so append and move on
            prevCollege=course.college
            sortCollege.append(course)
    return render_template('classSelector.html',courses=sortedCourses, selectedMajor=selectedMajor)

@login_required
@app.route('/schedule', methods=['GET'])
def schedule():
    return render_template('schedule.html', schedule=get_schedule())

##Actions
def get_courses_for_major(selectedMajor):
    #populate hardcoded classes from what we had in the drop down
    majorRequirements=['General University Requirements']
    if selectedMajor == 'CS':
        majorRequirements.append('Computer Science')
    elif  selectedMajor == 'IA':
        majorRequirements.append('Information Assurance')
    elif  selectedMajor == 'BIOI':
        majorRequirements.append('Bioinformatics')
    elif  selectedMajor == 'MIS':
        majorRequirements.append('Management Information Systems')
    else:
        majorRequirements=[]
    #Query for all the course requirement id's, now its more dynamic in case our DB changes
    requirements=model.Requirement.query.filter(model.Requirement.major.in_(majorRequirements)).all()
    #iterate through then database resposes to get the id's out
    requirementIdList=[]
    for requirement in requirements:
        requirementIdList.append(requirement.id)
    #query the database again with the id's we found to get out the classes required
    requirementNums=model.CourseRequirement.query.filter(model.CourseRequirement.requirement_id.in_(requirementIdList)).all()
    #pulling in all classes for the requirement given
    coursesToPull=[]
    for courseReq in requirementNums:
        coursesToPull.append(courseReq.course_id)
    #return a database object of the classes now
    return model.Course.query.filter(model.Course.id.in_(coursesToPull)).all()

def get_required_courses():
    major = "Computer Science"

    major_reqs = model.Requirement.query.filter(model.Requirement.major == major)
    uni_reqs = model.Requirement.query.filter(model.Requirement.major == "General University Requirements")
    all_reqs = list(major_reqs) + list(uni_reqs)

    # Get major specific requirements
    for req in all_reqs:
        classes = model.CourseRequirement.query.filter_by(requirement_id=req.id)

        needed_credits = req.credits/3
        if len(list(classes)) < needed_credits:
            logging.warn("Not enough credits to choose for {}-{}".format(req.major, req.name))
            needed_credits = len(list(classes))

        for c_req in random.sample(list(classes), needed_credits):
            yield ScheduledCourse(c_req.course, req)

def fix_prereqs(req_courses):
    schedule = collections.OrderedDict()

    reqs = sorted(req_courses, key=lambda x: x.course.ident)
    for r in reqs:
        # add prereqs to schedule
        for prereq in r.course.prereqs:
            if prereq not in schedule.keys():
                needed_course = model.Course.query.filter_by(number=prereq.split()[-1]).first()
                if needed_course:
                    schedule[needed_course.ident] = ScheduledCourse(needed_course, r.requirement)
                else:
                    logging.warn("Couldn't find prereq {}".format(prereq))
        schedule[r.course.ident] = r
    return schedule.values()

def get_schedule():
    listing = fix_prereqs(list(get_required_courses()))

    # yield chunks of 4
    classes_per_semester = 5
    for i in xrange(0, len(listing), classes_per_semester):
        yield listing[i:i+classes_per_semester]

##Misc
@login_required
@app.route('/js/<remainder>',methods=['GET'])
@app.route('/img/<remainder>',methods=['GET'])
def get_static(remainder):
    return send_from_directory(app.static_folder,request.path[1:])


app.secret_key = "Secret"

if __name__ == "__main__":
    app.run(host="0.0.0")
