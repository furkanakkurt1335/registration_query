import json, os, re, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.service import Service

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

credentials_path = f'{THIS_DIR}/credentials.json'
if not os.path.exists(credentials_path):
    print('Your credentials were not found.')
    should_exit = True
    response = input('If you would like to provide them now, enter y; otherwise n: ')
    username, password = 'Username', 'Password'
    if response == 'n':
        print('You need to add your credentials in "credentials.json" in the script folder.')
    elif response == 'y':
        username = input('Please enter your username: ')
        password = input('Please enter your password: ')
        should_exit = False
    else:
        print('Not a valid input. You need to add your credentials in "credentials.json" in the script folder.')
    with open(credentials_path, 'w', encoding='utf-8') as f:
        f.write('{"username": "%s", "password": "%s"}' % (username, password))
    if should_exit: exit()
with open(credentials_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
    if data['username'] == 'Username' or data['password'] == 'Password':
        print('You need to add your credentials in "credentials.json" in the script folder.'); exit()

username, password = data['username'], data['password']

login_url = 'https://registration.boun.edu.tr/buis/Login.aspx'
grade_url = 'https://registration.boun.edu.tr/scripts/stuinfar.asp'

env_folder = 'C:/env_executables'

chromedriver = Service(f"{env_folder}/chromedriver.exe")

desired = DesiredCapabilities.CHROME

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_experimental_option('excludeSwitches', ['enable-logging'])

driver = webdriver.Chrome(service=chromedriver, options=options, desired_capabilities=desired)

driver.get(login_url)

time.sleep(1)

driver.find_element(by=By.ID, value='txtUsername').send_keys(username)
driver.find_element(by=By.ID, value='txtPassword').send_keys(password)
driver.find_element(by=By.ID, value='btnLogin').click()

time.sleep(1)

driver.get(grade_url)

grades = {}

def strip_whitespace_section(s):
    s = s.replace('&nbsp;', '').replace('\t', '').replace('\n', '').replace(' ', '')
    if '.' in s: s = s[:s.index('.')]
    return s

grade_pattern = '<td width="14%">(.*?)</td>.*?<td width="7%">(.*?)</td>'
for course_grade in re.findall(grade_pattern, driver.page_source, re.DOTALL):
    grade, course = course_grade
    grade, course = strip_whitespace_section(grade), strip_whitespace_section(course)
    if grade not in grades.keys():
        grades[grade] = course

grades_path = f'{THIS_DIR}/grades.json'
if not os.path.exists(grades_path):
    with open(grades_path, 'w') as f:
        f.write('{}')

with open(grades_path, 'r') as f:
    prev_grades = json.load(f)

if prev_grades == dict():
    print('Initial run.')
    with open(f'{THIS_DIR}/grades.json', 'w') as f:
        json.dump(grades, f)
elif prev_grades != grades:
    for key in grades.keys():
        if key not in prev_grades.keys():
            print(f'New course added: {key}', end=' ')
            if grades[key] != '': print(f'with grade {grades[key]}', end='')
            print('')
        elif prev_grades[key] != grades[key]:
            print(f'{key} grade changed to {grades[key]}')
    with open(f'{THIS_DIR}/grades.json', 'w') as f:
        json.dump(grades, f)

driver.quit()