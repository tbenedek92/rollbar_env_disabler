# Read me
This script is intended to hide/unhide Rollbar environments autoamtically.

Run modes:
 1.  Set only the envs listed in the csv, to the given values in the csv
 2.  Hide everything, except what is set to unhide in the csv
 3.  Unhide everything, except what is set to hide in the csv

Rollbar username, password, account slug & project name can be read from environment variables
Automatic login only works with disabled MFA
At first run please provide the location of your chromedriver
