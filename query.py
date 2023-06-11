import json, os, re, time
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

credentials_path = os.path.join(THIS_DIR, 'credentials.json')
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
        json.dump({'username': username, 'password': password}, f, indent=4)
    if should_exit:
        exit()

with open(credentials_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
username, password = data['username'], data['password']

if username == 'Username':
    print('You need to add your credentials in "credentials.json" in the script folder.')
    exit()

login_url = 'https://registration.boun.edu.tr/buis/Login.aspx'
grade_url = 'https://registration.boun.edu.tr/scripts/stuinfar.asp'

options = ChromeOptions()
options.add_argument('--headless')
options.add_experimental_option('excludeSwitches', ['enable-logging'])

service = Service(ChromeDriverManager().install())

driver = Chrome(service=service, options=options)

driver.get(login_url)

time.sleep(1)

driver.find_element(by=By.ID, value='txtUsername').send_keys(username)
driver.find_element(by=By.ID, value='txtPassword').send_keys(password)
driver.find_element(by=By.ID, value='btnLogin').click()

time.sleep(1)

driver.get(grade_url)

grades = dict()

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

grades_path = os.path.join(THIS_DIR, 'grades.json')
if not os.path.exists(grades_path):
    with open(grades_path, 'w') as f:
        json.dump(dict(), f)

with open(grades_path, 'r') as f:
    prev_grades = json.load(f)

if prev_grades == dict():
    print('Initial run. Saving grades.')
    with open(grades_path, 'w') as f:
        json.dump(grades, f, indent=4)
elif prev_grades != grades:
    for course_id in grades.keys():
        if course_id not in prev_grades:
            if grades[course_id]:
                print('New course with the ID %s and grade %s' % (course_id, grades[course_id]))
            else:
                print('New course with the ID %s' % course_id)
        elif prev_grades[course_id] != grades[course_id]:
            if prev_grades[course_id]:
                print('Grade of %s changed from %s to %s' % (course_id, prev_grades[course_id], grades[course_id]))
            else:
                print('Grade of %s changed from None to %s' % (course_id, grades[course_id]))
    with open(grades_path, 'w') as f:
        json.dump(grades, f, indent=4)

driver.quit()