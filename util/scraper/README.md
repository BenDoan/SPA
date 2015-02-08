## Setup instructions
(1) Setup a virtualenv to install the dependencies:
```
virtualenv --no-site-packages -p /usr/bin/python2 env
```
(2) Activate the virtualenv (you'll need to do this before the script can be run):
```
source env/bin/activate
```
run `deactivate` to exit the virtualenv

(3) Install the dependencies with pip:
```
pip install -r requirements.txt
```
(4) Run the script:
```
python scraper.py > class_info.json
```

## Examples
```
source env/bin/activate
./scraper.py > uno_class_data.json
python scraper.py -l -c CSCI > csci_data.json
python scraper.py -l -c CSCI -o file.json
```

note: with my internet connection, the script takes about ~~30 minutes~~ 5 minutes (when run in parallel on 4 cores) to run for all terms and colleges
