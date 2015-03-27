from server import db, create_user, model
from sqlalchemy.exc import IntegrityError

import csv
import json
import os

def main():
    print "Creating tables..."
    db.drop_all()
    db.create_all()

    create_user('admin', 'admin@example.com', 'password')
    create_user('user', 'user@example.com', 'password')

    print "Ingesting class data..."
    insert_class_data('data/uno_class_data.json')

    print "Ingesting requirements data..."
    not_found_count = insert_requirements_data('data/ist_requirements')
    print "\nCouldn't find {} courses".format(not_found_count)

def insert_class_data(path):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    classes = json.load(file(path, 'r'))

    for term_number, term in classes.items():
        for college_name, college in term.items():
            for course_number, course in college.items():
                try:
                    nc = model.Course()
                    nc.number = course_number
                    nc.title = course['title']
                    nc.desc = course['desc']
                    nc.prereqs = course['prereq']
                    nc.college = college_name

                    db.session.add(nc)
                    db.session.commit()
                except IntegrityError:
                    # duplicate course, skip
                    db.session.rollback()

def insert_requirements_data(path):
    not_found_count = 0
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith('.csv'):
                not_found_count +=ingest_requirements_csv(os.path.join(root, f))
    return not_found_count

def ingest_requirements_csv(csv_file):
    not_found_count = 0

    reader = csv.reader(open(csv_file, 'r'), delimiter=',')

    requirement = next(reader)
    new_req = model.Requirement(requirement[0], requirement[1])
    db.session.add(new_req)

    for rule in reader:
        if '|' in rule[0]:
            continue

        course_college, course_number = rule[0].split()

        course = model.Course.query.filter_by(college=course_college,
                                number=course_number).first()
        if not course:
            print "Couldn't find course for {} {}".format(course_college, course_number)
            not_found_count+=1
            continue

        new_class_req = model.CourseRequirement(new_req, course)
    db.session.commit()
    return not_found_count

if __name__ == '__main__':
    main()
