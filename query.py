import json, os, re, time
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

print('Checking for updates in the registration system...')

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

manager = ChromeDriverManager(cache_valid_range=30).install()

service = Service(manager)

driver = Chrome(service=service, options=options)

driver.get(login_url)

time.sleep(1)

driver.find_element(by=By.ID, value='txtUsername').send_keys(username)
driver.find_element(by=By.ID, value='txtPassword').send_keys(password)
driver.find_element(by=By.ID, value='btnLogin').click()

time.sleep(1)

driver.get(grade_url)

def strip_whitespace_section(s, course=False):
    s = s.strip().replace('&nbsp;', '').replace('\t', '').replace('\n', '')
    while '  ' in s:
        s = s.replace('  ', ' ')
    if course and '.' in s:
        s = s[:s.index('.')]
    return s

semester_pattern = '\d{4}/\d{4}-\d{1}'
grades = dict()
soup = BeautifulSoup(driver.page_source, 'html.parser')
for row in soup.find_all('tr'):
    if row.find('td', {'width': '20%'}):
        text = row.find('td', {'width': '20%'}).text
        if 'Semester' in text:
            text = strip_whitespace_section(text)
            semester_search = re.search(semester_pattern, text)
            if semester_search:
                semester = semester_search.group(0)
    elif row.find('td', {'width': '14%'}):
        course_id = row.find('td', {'width': '14%'}).text
        course_grade = row.find('td', {'width': '7%'}).text
        course_id, course_grade = strip_whitespace_section(course_id, course=True), strip_whitespace_section(course_grade)
        if semester not in grades:
            grades[semester] = dict()
        grades[semester][course_id] = course_grade

grades_path = os.path.join(THIS_DIR, 'grades.json')
if not os.path.exists(grades_path):
    prev_grades = dict()
    with open(grades_path, 'w') as f:
        json.dump(prev_grades, f)
else:
    with open(grades_path, 'r') as f:
        prev_grades = json.load(f)

sem_l = list(grades.keys())
if len(sem_l) == 0:
    print('No semester found.')
    exit()
sem_l.sort(reverse=True)
latest_sem = sem_l[0]
latest_grades = grades[latest_sem]
latest_prev_grades = prev_grades[latest_sem]

if prev_grades == dict():
    print('Initial run. Saving grades.')
    with open(grades_path, 'w') as f:
        json.dump(grades, f, indent=4)
    print('Your latest semester is %s' % latest_sem)
    print('Grades:')
    for course_id in latest_grades:
        print('\t%s: %s' % (course_id, latest_grades[course_id]))
elif latest_grades == latest_prev_grades:
    print('No change in grades.')
elif latest_grades != latest_prev_grades:
    for course_id in latest_grades:
        if course_id not in latest_prev_grades:
            if grades[course_id]:
                print('New course with the ID %s and grade %s' % (course_id, latest_grades[course_id]))
            else:
                print('New course with the ID %s' % course_id)
        elif latest_prev_grades[course_id] != latest_grades[course_id]:
            if latest_prev_grades[course_id]:
                print('Grade of %s changed from %s to %s' % (course_id, latest_prev_grades[course_id], latest_grades[course_id]))
            else:
                print('Grade of %s changed from None to %s' % (course_id, latest_grades[course_id]))
    with open(grades_path, 'w') as f:
        json.dump(grades, f, indent=4)

driver.quit()