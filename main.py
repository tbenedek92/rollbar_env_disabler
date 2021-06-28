from selenium import webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os

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


def open_env_page(driver, rb_account_name, rb_project_name ):
    driver.get(f'https://rollbar.com/{rb_account_name}/{rb_project_name}/settings/environments/')
    wait = ui.WebDriverWait(driver, 10) # timeout after 10 seconds
    results = wait.until(lambda driver: driver.find_elements_by_id('Environments'))

    table_id = driver.find_element(By.ID, 'Environments')
    rows = table_id.find_elements(By.TAG_NAME, "tr")
    rows.pop(0)     # dropping the header of the table
    for row in rows:
        try:
            btn = row.find_elements(By.CLASS_NAME, "toggle-btn")[0]
            btn.click()
        except IndexError:
            pass

    for result in results:
        print(result.text)


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
    ROLLBAR_ACCOUNT = input('Please provide your Rollbar account slug. If you login to your Rollbar account, '
                            'you may copy it from the URL  https://rollbar.com/{yourrollbaraccountslug}')
    ROLLBAR_PROJECT = input("Please provide your Rollbar project's slug. You can check it in the following url"
                            "https://rollbar.com/{yourrollbaraccountslug}/settings/projects")


if __name__ == '__main__':
    set_credentials_from_env_vars()
    driver = open_webdriver()
    rb_sign_in(driver)
    open_env_page(driver, 'benedek-test', 'env_test')
