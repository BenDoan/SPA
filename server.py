from flask import *

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask.ext.assets import Environment, Bundle
from htmlmin import minify
from flask.ext.login import LoginManager,login_user,logout_user, current_user, login_required
from flask_wtf import Form
from wtforms import StringField, PasswordField, TextField, TextAreaField
from wtforms import validators
from passlib.hash import pbkdf2_sha256
from operator import itemgetter

import random
import logging
import collections
import urllib
import json

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

css = Bundle('css/main.css', 'css/bootstrap.css', filters="cssmin", output='css/gen/packed.css')
assets.register('css_all', css)

model = Model(app)
db = model.db

## Authentication
class LoginForm(Form):
    name = StringField('name', validators=[validators.DataRequired()])
    password = PasswordField('password', validators=[validators.DataRequired()])

class SignupForm(Form):
    name = StringField('name', validators=[validators.DataRequired()])
    email = StringField('email', validators=[validators.DataRequired()])
    password = PasswordField('password', validators=[validators.DataRequired()])
    repeatpassword = PasswordField('repeatpassword', validators=[validators.DataRequired()])

class AddRoomForm(Form):
    title = TextField('title', validators=[validators.DataRequired()])
    number = TextField('number', validators=[validators.DataRequired()])
    short_description = TextAreaField('short_description', validators=[validators.DataRequired()])
    long_description = TextAreaField('long_description', validators=[validators.DataRequired()])
    image = TextField('image', validators=[validators.DataRequired()])

class EditUserForm(Form):
    name = TextField('name')
    email = TextField('email')
    password = PasswordField('password', [
       validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat password')

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
        if user != None:
            if pbkdf2_sha256.verify(request.form["password"],user.password) :
                user.authenticated = True
                db.session.commit()
                login_user(user)
                return redirect("/")
        error = "incorrect username or password"
    return render_template("signin.html", form=form, error=error);

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

def get_current_user():
    return current_user

@login_required
@app.route('/deleteSchedule')
def deleteSchedule():
    current_user.schedule=""
    db.session.commit()
    flash("User Schedule Deleted", "success")
    return redirect('/')

##Content
@login_required
@app.route('/', methods=['GET'])
def index():
    if current_user.is_anonymous():
        return redirect("/signin")

    #Made this global so I can use it throughout the site
    #userSchedule=False
    #if current_user.schedule:
    #    userSchedule=True

    return render_template('index.html',userSchedule=hasSchedule())

@login_required
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == "POST":
        form = EditUserForm()
        if not form.validate_on_submit():
            for error in form.errors:
                flash("Error for {}".format(error), "danger")
            return render_template("profile.html", form=form)

        current_user.username = form.name.data
        current_user.email = form.email.data
        if form.password.data.strip() != "":
            current_user.password = pbkdf2_sha256.encrypt(form.password.data)
        db.session.commit()
        flash("User updated", "success")
    return render_template('profile.html', form=EditUserForm(), userSchedule=hasSchedule())

@login_required
@app.route('/classSelector',methods=['GET'])
def class_selector():
    selectedMajor = request.args.get('majorSelected', 'None')
    creditNum = request.args.get('creditNum', 'None')
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
    return render_template('classSelector.html',courses=sortedCourses, selectedMajor=selectedMajor, creditNum=creditNum)

@login_required
@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if request.method == 'POST':
        selected_hist = json.loads(urllib.unquote(request.form.get("user_history", "")))
        if selected_hist == "" or "classes" not in selected_hist:
            logging.warn("Bad user history: {}".format(selected_hist))
            abort(400)

        major = selected_hist["options"][0]["majorSelected"]
        creditsLoad = selected_hist['options'][0]['creditsLoad']
        if creditsLoad == 'None':
            creditsLoad = 15
        classesLoad = int(creditsLoad)/3

        history = []
        for college, courses in selected_hist["classes"][0].items():
            for course in courses:
                c = model.Course.query.filter_by(college=college, number=course).first()
                if c:
                    history.append(c)
                else:
                    flash("Couldn't find course: {} {}".format(college, course), "warning")

        generatedSchedule=get_schedule(major, history, classesLoad)
        formattedSchedule=[]
        for semester in generatedSchedule:
            singleSemester=[]
            for cls in semester:
                singleSemester.append({'course':{'title':cls.course.title, 'ident':cls.course.ident, 'credits':cls.course.credits}})
            formattedSchedule.append(singleSemester)
        pushClasslistToDB(formattedSchedule)
        return render_template('schedule.html', schedule=formattedSchedule)
    elif request.method == 'GET':
        #flash("Generating schedule with no user history", "info")
        return render_template('schedule.html', schedule=getClasslistFromDB())


@login_required
@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

##Actions
def hasSchedule():
    if current_user.schedule:
        return True
    return False

def pushClasslistToDB(generatedSchedule):
    current_user.schedule=json.dumps(generatedSchedule)
    db.session.commit()

def getClasslistFromDB():
    if current_user.schedule:
        return json.loads(current_user.schedule)
    else:
        return ""

def get_courses_for_major(selectedMajor):
    majorRequirements = ['General University Requirements', selectedMajor]
    if selectedMajor == 'None':
        majorRequirements = []

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

def get_required_courses(major, history=None):
    major_reqs = model.Requirement.query.filter(model.Requirement.major == major)
    uni_reqs = model.Requirement.query.filter(model.Requirement.major == "General University Requirements")
    all_reqs = list(major_reqs) + list(uni_reqs)

    # Get major specific requirements
    for req in all_reqs:
        courses = [x.course for x in model.CourseRequirement.query.filter_by(requirement_id=req.id)]

        needed_credits = req.credits
        have_credits = sum((x.credits for x in courses))
        if have_credits < needed_credits:
            #FIXME handle this case better
            logging.warn("Not enough credits to choose for {}-{}".format(req.major, req.name))

            needed_credits = have_credits

        taken_credits = 0
        while taken_credits < needed_credits:
            random_course = random.sample(courses, 1)[0]

            taken_credits += random_course.credits
            if history and random_course in history:
                continue
            else:
                yield ScheduledCourse(random_course, req)

def fix_prereqs(req_courses, history):
    schedule = collections.OrderedDict()
    history = [x.ident for x in history] if history else []

    classes_checked = {}
    recheck = []
    def add_prereqs(reqs):
        for r in reqs:
            # add prereqs to schedule
            for prereq in r.course.prereqs:
                if prereq not in schedule.keys() and prereq not in history:
                    c, n = prereq.split()
                    needed_course = model.Course.query.filter_by(college=c, number=n).first()
                    if needed_course:
                        schedule[needed_course.ident] = ScheduledCourse(needed_course, r.requirement)
                        recheck.append(needed_course)
                    else:
                        logging.warn("Couldn't find prereq {}".format(prereq))
            classes_checked[r.course.ident] = True
            schedule[r.course.ident] = r

    reqs = sorted(req_courses, key=lambda x: x.course.ident)
    add_prereqs(reqs)

    while len(classes_checked) != len(schedule):
        while recheck:
            add_prereqs([ScheduledCourse(recheck.pop(), None)])

    return schedule.values()

def get_schedule(major, history=None, classes_per_semester=5):
    listing = fix_prereqs(list(get_required_courses(major, history)), history)

    #FIXME make sure prereqs are separated by at least a semester
    # yield chunks of 4
    #classes_per_semester = 5 #going to get passed instead
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
