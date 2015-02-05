#!/usr/bin/env python

from BeautifulSoup import BeautifulSoup
import requests
import json

def main():
    page = requests.get("http://www.unomaha.edu/class-search/?term=1151&session=&subject=ANTH&catalog_nbr=&career=&instructor=&class_start_time=&class_end_time=&location=&special=&instruction_mode=")
    soup = BeautifulSoup(page.text)

    classes = []
    for dotted in soup.findAll("div", {'class': 'dotted-bottom'}):
        cls = {}

        number = dotted.find("h2")
        if number:
            cls['number'] = number.text

        title = dotted.find("p")
        if title:
            cls['title'] = title.text

        desc = dotted.findAll("p")
        if len(desc) > 1:
            cls['desc'] = desc[1].text

        if len(desc) > 2:
            cls['prereq'] = desc[2].text

        class_attrs = {}
        table = dotted.find("table")
        if table:
            rows = table.findAll("tr")
            for tr in rows:
                tds = tr.findAll("td")
                if tds:
                    if len(tds) > 1:
                        class_attrs[tds[0].text] = tds[1].text
        cls['attrs'] = class_attrs
        classes.append(cls)

    print json.dumps(classes)

if __name__ == "__main__":
    main()
