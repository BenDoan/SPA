#!/usr/bin/env python2

"""
Usage:
    ./scraper.py [options]

Options:
    -h, --help                      Prints this help message
    -o FILE, --output FILE          Specifies output file
    -c COLLEGE, --college COLLEGE   Specifies a specific college
    -l, --last-term-only            Only ouputs the last term
    -u URL, --url URL               Specify an alternate class-search url
    -v, --verbose                   Turns on verbose logging
"""

import json
import itertools

from collections import OrderedDict
from multiprocessing import Pool, cpu_count

import requests
import logging

from docopt import docopt
from BeautifulSoup import BeautifulSoup

BASE_URL = "http://www.unomaha.edu/registrar/students/before-you-enroll/class-search/"

colleges = ["CSCI"]
with open("data/colleges.json") as f:
    colleges = json.loads(f.readline())

terms = [1155]
with open("data/terms.json") as f:
    terms = json.loads(f.readline())

def get_college_data((college, term)):
    """Returns a dictionary containing all classes within college and term"""
    logging.info("Processing college {}".format(college))

    page = requests.get("{}?term={}&session=&subject={}&catalog_nbr=&career=&instructor=&class_start_time=&class_end_time=&location=&special=&instruction_mode=".format(BASE_URL, term,  college))
    soup = BeautifulSoup(page.text)

    classes = OrderedDict()

    if len(soup.findAll("div", {'class': 'dotted-bottom'})) == 0:
        logging.error("No classes for college {}, term {}".format(college, term))

    #loop through each class in the college
    for dotted in soup.findAll("div", {'class': 'dotted-bottom'}):
        cls = OrderedDict()

        number = dotted.find("h2")
        if number:
            class_number = number.text.split(" ")[-1]
        else:
            class_number = "-"

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

        sections = OrderedDict()
        tables = dotted.findAll("table")
        if tables:
            # loop through each section in the class
            for table in tables:
                section = OrderedDict()
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

        if class_number != "-":
            classes[class_number] = cls

    return classes

def get_full_term_listing():
    """Returns a dictionary containing the uno classes
    for every listed term and college"""
    pool = Pool(cpu_count()*2)

    term_data = OrderedDict()
    for term in terms:
        logging.info("Processing term {}".format(term))

        results = pool.map(get_college_data, zip(colleges, itertools.repeat(term)))
        term_data[term] = OrderedDict(zip(colleges, results))
    return term_data


def _main():
    args = docopt(__doc__, version="1")

    # process arguments
    if args['--college'] is not None:
        global colleges
        colleges = [args['--college']]

    if args['--last-term-only']:
        global terms
        terms = [terms[-1]]

    if args['--url']:
        global URL
        URL = args['--url']

    if args['--verbose']:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    term_data = get_full_term_listing()

    # output class data as json
    json_data = json.dumps(term_data, sort_keys=False, indent=4, separators=(',', ': '))
    if args['--output'] is not None:
        with open(args['--output'], 'w') as f:
            f.write(json_data)
    else:
        print json_data

if __name__ == "__main__":
    _main()
