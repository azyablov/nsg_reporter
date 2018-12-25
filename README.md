# Intro
This script intended to generate report about NSG exists in Nuage VSD.
API version is 5.0.
Tested with Nuage 5.2.3_131.

# Installation

git clone https://github.com/azyablov/nsg_reporter.git
pip install -r requirements.txt

# Usage
usage: nsg_reporter.py [-h] -v V [-l L] [-p P] [--csv] [--xlsx XLSX] [--show]

nsg_reporter.py script connects to VSD to retrieve NSG objects and attributes
and generate status report for all enterprises in form of XLSX, CSV or just
print it into console in as pretty text format

optional arguments:
  
  -h, --help   show this help message and exit
  
  -v V         VSD IP address or FQDN
  
  -l L         user login [csproot rights]
  
  -p P         csproot password
  
  --csv        print report in stdout in CSV format
  
  --xlsx XLSX  create report in XLSX format, file name should be provided
  
  --show       show pretty text report in stdout



