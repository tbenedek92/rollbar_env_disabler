from selenium import webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import csv
from time import sleep


'''
This script is intended to hide/unhide Rollbar environments autoamtically.

run modes:
 1.  Set only the envs listed in the csv, to the given values in the csv
 2.  Hide everything, except what is set to unhide in the csv
 3.  Unhide everything, except what is set to hide in the csv

Rollbar username, password, account slug & project name can be read from environment variables
Automatic login only works with disabled MFA
At first run please provide the location of your chromedriver

'''

RUN_MODE = 1

CHROMEDRIVER_LOCATION_CACHE_FILE = "chromedriver_location.txt"
ROLLBAR_USERNAME = None
ROLLBAR_PASSWORD = None

ROLLBAR_ACCOUNT = None
ROLLBAR_PROJECT = None


def open_webdriver():
    location_cache_exists = os.path.isfile(CHROMEDRIVER_LOCATION_CACHE_FILE)
    if location_cache_exists:
        with open(CHROMEDRIVER_LOCATION_CACHE_FILE, "r") as file:
            chromedriver_location = file.readline()
        file.close()

    else:
        print('Please provide the location for chromedriver! Download it from: https://chromedriver.chromium.org/')
        chromedriver_location = input()
    wdriver = webdriver.Chrome(chromedriver_location)
    if not location_cache_exists:
        f = open(CHROMEDRIVER_LOCATION_CACHE_FILE, 'x')
        f.write(chromedriver_location)
        f.close()
    return wdriver


def open_env_page(driver, desired_state_dict):
    driver.get(f'https://rollbar.com/{ROLLBAR_ACCOUNT}/{ROLLBAR_PROJECT}/settings/environments/')
    wait = ui.WebDriverWait(driver, 10) # timeout after 10 seconds
    results = wait.until(lambda driver: driver.find_elements_by_id('Environments'))
    sleep(8)
    table_id = driver.find_element(By.ID, 'Environments')
    rows = table_id.find_elements(By.TAG_NAME, "tr")
    rows.pop(0)     # dropping the header of the table
    for row in rows:
        row_text = repr(row.text).partition('\\n')
        env_name = row_text[0][1:]
        env_current_state = row_text[2][:-1]
        # if True returned button will be clicked
        click_action_required = click_action_logic(desired_state_dict, env_name, env_current_state)

        if click_action_required:
            btn = row.find_elements(By.CLASS_NAME, "toggle-btn")[0]
            btn.click()


def click_action_logic(desired_state_dict, env_name, env_current_state):
    if RUN_MODE == 1:
        try:
            if desired_state_dict[env_name] == env_current_state:
                return False
            else:
                return True
        except KeyError:
            return False
    elif RUN_MODE == 2:
        if env_name not in desired_state_dict.keys() and env_current_state.lower() != 'hidden':
            return True
        if env_name not in desired_state_dict.keys() and env_current_state.lower() == 'hidden':
            return False
        if desired_state_dict[env_name] == env_current_state:
            return False
        else:
            return True
    elif RUN_MODE == 3:
        if env_name not in desired_state_dict.keys() and env_current_state.lower() != 'visible':
            return True
        if env_name not in desired_state_dict.keys() and env_current_state.lower() == 'visible':
            return False
        if desired_state_dict[env_name] == env_current_state:
            return False
        else:
            return True

def rb_sign_in(driver):
    driver.get('https://rollbar.com/login')
    ui.WebDriverWait(driver, 10) # timeout after 10 seconds
    ui.WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username_or_email")))
    # autoamted login if env vars are set & 2fa not enabled
    if ROLLBAR_USERNAME is not None and ROLLBAR_PASSWORD is not None:
        username_field = driver.find_element_by_name('username_or_email')
        username_field.send_keys(ROLLBAR_USERNAME)
        passsword_field = driver.find_element_by_name('password')
        passsword_field.send_keys(ROLLBAR_PASSWORD)
        passsword_field.submit()
    else:
        input('Please login to Rollbar with your credentials, then press Enter to continue...')

    ui.WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "NavBar")))


def set_credentials_from_env_vars():
    global ROLLBAR_USERNAME
    global ROLLBAR_PASSWORD

    try:
        ROLLBAR_USERNAME = os.environ['ROLLBAR_USERNAME']
    except KeyError:
        print('ROLLBAR_USERNAME environment variable is not set, manual login triggered.')
        return
    try:
        ROLLBAR_PASSWORD = os.environ['ROLLBAR_PASSWORD']
    except KeyError:
        print('ROLLBAR_PASSWORD environment variable is not set, manual login triggered.')


def set_account_project():
    global ROLLBAR_ACCOUNT
    global ROLLBAR_PROJECT

    try:
        ROLLBAR_ACCOUNT = os.environ['ROLLBAR_ACCOUNT']
    except KeyError:
        ROLLBAR_ACCOUNT = input('Please provide your Rollbar account slug. If you login to your Rollbar account, '
                                'you may copy it from the URL  https://rollbar.com/{yourrollbaraccountslug}')
    try:
        ROLLBAR_PROJECT = os.environ['ROLLBAR_PROJECT']
    except KeyError:
        ROLLBAR_PROJECT = input("Please provide your Rollbar project's slug. You can check it in the following url"
                                "https://rollbar.com/{yourrollbaraccountslug}/settings/projects")




def set_run_mode():
    global RUN_MODE

    print('Please select a run mode: \n'
          ' 1.  Set only the envs listed in the csv, to the given values in the csv \n'
          ' 2.  Hide everything, except what is set to unhide in the csv \n'
          ' 3.  Unhide everything, except what is set to hide in the csv')
    run_mode_temp = input()
    run_mode_verification_failed = True
    while run_mode_verification_failed:
        try:
            run_mode_temp = int(run_mode_temp)
        except ValueError:
            pass
        if isinstance(run_mode_temp, int) and 1 <= run_mode_temp <= 3:
            break
        print('The given value must be between 1, 2 or 3.')
        run_mode_temp = input()
    RUN_MODE = run_mode_temp


def read_csv(env_csv_file):
    desired_state_dict = {}
    if os.path.isfile(env_csv_file):
        with open(env_csv_file, mode='r', encoding='utf-8-sig') as csvfile:
            update_env_csv = csv.reader(csvfile, delimiter=',')
            for row in update_env_csv:
                desired_state_dict[row[0]] = row[1]
        csvfile.close()
    else:
        print('update_env.csv file does not exist. Please make sure to create one, before running the script.')
        exit(0)
    return desired_state_dict

if __name__ == '__main__':
    desired_state_dict = read_csv('update_env.csv')
    set_run_mode()
    set_account_project()
    set_credentials_from_env_vars()
    driver = open_webdriver()
    rb_sign_in(driver)
    open_env_page(driver, desired_state_dict)
