#!/usr/bin/python3
from canvascourses import courses
import requests, json, sys, re

try:
	fh = open('hemlig-nyckel.txt', 'r')
	access_token = fh.read().strip()
	fh.close()

except:
	print('misslyckades med att läsa in den hemliga nyckeln')
	print('generera med nyckelskapare.py')
	sys.exit(1)

base = 'https://kth.instructure.com/api/v1'


def get_list(url):
	response = []
	
	while url is not None:
		if not url.startswith(base): url = base + url
		
		if '?' in url: url = url.replace('?', '?per_page=50&')
		else: url += '?per_page=50'
		
		response_this = requests.get(url = url, headers = { 'Authorization': 'Bearer ' + access_token })
		response_list = response_this.json()
		
		if type(response_list) is not list: return response_list
		
		response += response_list
	
		url = None
	
		if 'Link' in response_this.headers:
			r = re.search('<([^>]+?)>; rel="next"', response_this.headers['Link'])
		
			if r is not None: url = r.group(1)
		
	return response


def get_object(url):
	return requests.get(url = base + url, headers = { 'Authorization': 'Bearer ' + access_token }).json()


def put(url, data):
	return requests.put(url = base + url, headers = { 'Authorization': 'Bearer ' + access_token }, data = data).json()


def post(url, data):
	return requests.post(url = base + url, headers = { 'Authorization': 'Bearer ' + access_token }, data = data).json()


def grade2api(grade, assignment):
	if grade == '-': return ''
	
	if assignment['grading_type'] == 'pass_fail':
		if grade == 'P' or grade == 'p': return 'complete'
		if grade == 'F' or grade == 'f': return 'incomplete'
		
		return None
	
	if assignment['grading_type'] == 'points':
		try:
			grade = int(grade)
		
			if grade < 0: return None
			
			return str(grade)
	
		except:
			return None
	
	if assignment['grading_type'] == 'letter_grade':
		valid_grade = None
		
		for x in assignment['grading_scheme']:
			if x.casefold() == grade.casefold():
				valid_grade = x
				break
		
		return valid_grade
	
	else:
		return None


if len(sys.argv) != 3:
	print('kör så här: klump.py <kursnamn> <filnamn>')
	sys.exit(1)

if sys.argv[1] not in courses:
	print('hittade ej angiven kurs')
	sys.exit(1)

try:
	fh = open(sys.argv[2], 'r')
	lines = fh.readlines()
	fh.close()

except:
	print('kunde ej öppna angiven fil')
	sys.exit(1)


columns_raw = lines[0].split('\t')
lines.pop(0)

student_column_id = None
columns = {}

line_length = len(columns_raw)
i = 0

while i < len(columns_raw):
	if columns_raw[i] == 'ID':
		if student_column_id is not None:
			print('det finns flera kolumner med ID')
			sys.exit(1)
		
		student_column_id = i
	
	else:
		assignment_id = re.search('\(([0-9]+)\)$', columns_raw[i])
		
		if assignment_id is not None:
			assignment_id = int(assignment_id.group(1))
			
			if assignment_id in columns.values():
				print('det finns flera kolumner som avser uppgift ' + str(assignment_id))
				sys.exit(1)
			
			columns[i] = assignment_id
	
	i += 1

tasks = []
used_students = {}
i = -1

while i < len(lines) - 1:
	i += 1
	line = lines[i].split('\t')
	
	if len(line) == 1: continue
	
	if len(line) != line_length:
		print('rad ' + str(i + 2) + ' har ' + str(len(line)) + ' kolumner, och inte ' + str(line_length) + ' kolumner')
		sys.exit(1)
	
	student_id = line[student_column_id].strip()
	
	if len(student_id) == 0:
		print('rad ' + str(i + 2) + ' ignoreras eftersom den saknar student-ID')
		continue
	
	try:
		student_id = int(student_id)
	
	except:
		print('rad ' + str(i + 2) + ' har ett ogiltigt student-ID')
		sys.exit(1)
	
	if student_id in used_students:
		print('rad ' + str(i + 2) + ' har en student som har förekommit på en tidigare rad')
		sys.exit(1)
	
	used_students[student_id] = i + 2
	
	for index in columns:
		grade = line[index].strip()
		if len(grade) == 0: continue
		
		tasks.append({
			'line': i + 2,
			'student_id': student_id,
			'assignment_id': columns[index],
			'grade': grade
		})

course = courses[sys.argv[1]]

print('läser in uppgifter')

assignments = get_list('/courses/' + str(course) + '/assignments')

if 'errors' in assignments:
	print('fel vid inläsning av uppgifter -- kanske fel API-nyckel eller fel kurs-ID?')
	print(assignments['errors'])
	sys.exit(1)


assignments = [assignment for assignment in assignments if assignment['published'] and (assignment['grading_type'] == 'pass_fail' or assignment['grading_type'] == 'points' or assignment['grading_type'] == 'letter_grade')]

grading_standards = {}

for assignment in assignments:
	if assignment['grading_standard_id'] is not None:
		gsi = assignment['grading_standard_id']
		
		if gsi not in grading_standards:
			grading_standards[gsi] = [grade['name'] for grade in get_object('/courses/' + str(course) + '/grading_standards/' + str(gsi))['grading_scheme']]
		
		assignment['grading_scheme'] = grading_standards[gsi]

if len(assignments) == 0:
	print('hittade inga uppgifter')
	sys.exit(1)


assignments_dict = {}
for a in assignments: assignments_dict[a['id']] = a
assignments = assignments_dict


print('läser in studenter')

students = get_list('/courses/' + str(course) + '/users?enrollment_type[]=student')

if len(students) == 0:
	print('hittade inga studenter')
	sys.exit(1)

for assignment_id in columns.values():
	if assignment_id not in assignments:
		print('okänt uppgifts-ID ' + str(assignment_id) + ' i tabellhuvudet')
		sys.exit(1)

for student_id in used_students:
	if student_id not in [s['id'] for s in students]:
		print('okänt student-ID ' + str(student_id) + ' på rad ' + str(used_students[student_id]))
		sys.exit(1)

error = False

for task in tasks:
	grade = grade2api(task['grade'], assignments[task['assignment_id']])
	
	if grade is None:
		print('felaktigt resultat \'' + task['grade'] + '\' på rad ' + str(task['line']))
		error = True
	
	task['grade'] = grade

if error: sys.exit(1)

print('skriv \'OK\' för att rapportera in ' + str(len(tasks)) + ' resultat')

command = input('>> ')

if command.lower() != 'ok':
	print('avbryter och avslutar')
	sys.exit(1)

for assignment in assignments:
	assignment = assignments[assignment]
	data = {}
	
	for task in tasks:
		if task['assignment_id'] != assignment['id']: continue
		data['grade_data[' + str(task['student_id']) + '][posted_grade]'] = task['grade']
	
	if len(data) == 0: continue

	print('skriver ' + str(len(data)) + ' resultat till ' + assignment['name'])
	
	result = post('/courses/' + str(course) + '/assignments/' + str(assignment['id']) + '/submissions/update_grades', data)
	
	if 'errors' in result:
		print('fel från Canvas:')
		print(result)
