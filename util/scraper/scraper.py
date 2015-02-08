#!/usr/bin/env python2

"""
Usage:
    ./scraper.py [options]

Options:
    -h, --help                      Prints this help message
    -o FILE, --output FILE          Specifies output file
    -c COLLEGE, --college COLLEGE   Specifies a specific college
    -l, --last-term-only            Only ouputs the last term
    -v, --verbose                   Turns on verbose logging
"""

import json
import collections

import requests
import logging

from docopt import docopt
from BeautifulSoup import BeautifulSoup

BASE_URL = "http://www.unomaha.edu/class-search/"

colleges = ["CSCI"]
with open("data/colleges.json") as f:
    colleges = json.loads(f.readline())

terms = [1151]
with open("data/terms.json") as f:
    terms = json.loads(f.readline())


def get_college_data(college, term):
    page = requests.get("{}?term={}&session=&subject={}&catalog_nbr=&career=&instructor=&class_start_time=&class_end_time=&location=&special=&instruction_mode=".format(BASE_URL, term,  college))
    soup = BeautifulSoup(page.text)

    classes = collections.OrderedDict()
    for dotted in soup.findAll("div", {'class': 'dotted-bottom'}):
        cls = collections.OrderedDict()

        number = dotted.find("h2")
        if number:
            cls['number'] = number.text.split(" ")[-1]
        else:
            cls['number'] = "-"

        title = dotted.find("p")
        if title:
            cls['title'] = title.text
        else:
            cls['title'] = "-"

        desc = dotted.findAll("p")
        if len(desc) > 1:
            cls['desc'] = desc[1].text
        else:
            cls['desc'] = "-"

        if len(desc) > 2:
            cls['prereq'] = desc[2].text
        else:
            cls['prereq'] = "-"

        sections = collections.OrderedDict()
        tables = dotted.findAll("table")
        if tables:
            for table in tables:
                section = collections.OrderedDict()
                rows = table.findAll("tr")
                for tr in rows:
                    tds = tr.findAll("td")
                    if tds:
                        if len(tds) > 1 and tds[1].text != "Date": # remove weird field
                            section[tds[0].text] = tds[1].text
                section_name = table.find("th")
                if section_name:
                    section_num = section_name.text.split(" ")[-1]
                    sections[section_num] = section

        cls['sections'] = sections

        if 'number' in cls and cls['number'] != "-":
            classes[cls['number']] = cls

    return classes


def main():
    args = docopt(__doc__, version="1")

    if args['--college'] is not None:
        global colleges
        colleges = [args['--college']]

    if args['--last-term-only']:
        global terms
        terms = [terms[-1]]

    if args['--verbose']:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)


    term_data = collections.OrderedDict()
    for term in terms:
        logging.info("Processing {}".format(term))
        college_data = collections.OrderedDict()
        for college in colleges:
            logging.info("Processing {}".format(college))
            college_data[college] = get_college_data(college, term)

        term_data[term] = college_data

    json_data = json.dumps(term_data, sort_keys=False, indent=4, separators=(',', ': '))
    if args['--output'] is not None:
        with open(args['--output'], 'w') as f:
            f.write(json_data)
    else:
        print json_data

if __name__ == "__main__":
    main()