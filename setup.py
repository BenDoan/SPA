from server import db, create_user, model

import json
import os

def main():
    db.drop_all()
    db.create_all()

    create_user('admin', 'admin@example.com', 'password', is_admin=True)
    create_user('user', 'user@example.com', 'password', is_admin=False)

    insert_class_data('util/scraper/uno_class_data.json')

def insert_class_data(path):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    classes = json.load(file(path, 'r'))

    for term_number, term in classes.items():
        for college_name, college in term.items():
            for course_number, course in college.items():
                nc = model.Course()
                nc.number = course_number
                nc.title = course['title']
                nc.desc = course['desc']
                nc.prereqs = course['prereq']
                nc.college = college_name

                db.session.add(nc)
                db.session.commit()

if __name__ == '__main__':
    main()
