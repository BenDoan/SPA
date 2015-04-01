from server import db, create_user, model
from sqlalchemy.exc import IntegrityError

import csv
import json
import os

def main():
    output_requirements_data('data/ist_requirements')

def output_requirements_data(path):
    not_found_count = 0
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith('.csv'):
                ingest_requirements_csv(os.path.join(root, f))

def ingest_requirements_csv(csv_file):
    reader = csv.reader(open(csv_file, 'r'), delimiter=',')

    requirement = next(reader)
    req_name, req_credits = requirement

    print '"' + req_name + '":'
    cat = {"credits": req_credits, "classes": []}

    for rule in reader:
        cls = {"name": rule[0], "rating": 3}
        cat['classes'].append(cls)
    print json.dumps(cat, indent=4, separators=(',', ': '))


if __name__ == '__main__':
    main()
