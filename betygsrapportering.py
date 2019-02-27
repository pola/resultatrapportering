#!/usr/bin/python3
from config import access_token, courses
import requests, json, sys, re

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


if len(sys.argv) != 2:
	print('kör så här: betygsrapportering.py <kursnamn>')
	sys.exit(1)

if sys.argv[1] not in courses:
	print('hittade ej angiven kurs')
	sys.exit(1)

course = courses[sys.argv[1]]

assignments = get_list('/courses/' + str(course) + '/assignments')

if 'errors' in assignments:
	print('fel vid inläsning av uppgifter -- kanske fel API-nyckel eller fel kurs-ID?')
	print(assignments['errors'])
	sys.exit(1)

assignments = [assignment for assignment in assignments if assignment['published'] and (assignment['grading_type'] == 'pass_fail' or assignment['grading_type'] == 'points' or assignment['grading_type'] == 'letter_grade')]

for assignment in assignments:
	if assignment['grading_standard_id'] is not None:
		grading_standard = get_object('/courses/' + str(course) + '/grading_standards/' + str(assignment['grading_standard_id']))
		
		assignment['grading_scheme'] = [grade['name'] for grade in grading_standard['grading_scheme']]

if len(assignments) == 0:
	print('hittade inga uppgifter')
	sys.exit(1)


def nice_student(student):
	return student['short_name'] + ' <' + student['email'] + '>'


def nice_grade(grade):
	if grade is None: return '-'
	
	grade = str(grade)

	if grade == 'incomplete': return 'F'
	if grade == 'complete': return 'P'
	
	return grade


def choose_assignment(student):
	fetch_grades = True
	
	while True:
		if fetch_grades:
			current_grades = {}
			
			submissions = get_list('/courses/' + str(course) + '/students/submissions?student_ids[]=' + str(student['id']))
	
			for submission in submissions:
				current_grades[submission['assignment_id']] = submission['grade']
		
		print('\nvälj uppgift för ' + nice_student(student) + ':')
		print('index  betyg  uppgift')
	
		i = 1
		for assignment in assignments:
			current_grade = nice_grade(current_grades[assignment['id']]) if assignment['id'] in current_grades else '-'
			
			print('{0: <6}'.format(str(i)), end = ' ')
			print('{0: <7}'.format(current_grade), end = '')
			print(assignment['name'])
			i += 1
	
		choice = input('>> ')
	
		if len(choice) == 0:
			return
	
		try:
			choice = int(choice)
		
			if choice < 1 or choice > len(assignments):
				print('ogiltigt val, försök igen')
				continue
		
			assignment_choice = assignments[choice - 1]
	
		except:
			assignment_choice = None
		
			for assignment in assignments:
				if assignment['name'] == choice:
					assignment_choice = assignment
					break
		
			if assignment_choice is None:
				print('ogiligt val, försök igen')
				continue
	
		fetch_grades = set_grade(student, assignment_choice)


def set_grade(student, assignment):
	if assignment['grading_type'] == 'pass_fail' or assignment['grading_type'] == 'points' or assignment['grading_type'] == 'letter_grade': t = assignment['grading_type']
	else: raise Exception
	
	while True:
		print()
		
		if t == 'pass_fail': print('skriv in betyget (P, F, -):')
		elif t == 'points': print('skriv in betyget (0 .. , -):')
		elif t == 'letter_grade': print('skriv in betyget (' + (', '.join(assignment['grading_scheme'])) + ', -):')
		
		grade = input('>> ')
		
		if len(grade) == 0:
			print('avbryter')
			return False
		
		if grade == '-':
			grade = ''
		
		else:
			if t == 'pass_fail':
				if grade == 'P' or grade == 'p':
					grade = 'complete'
				
				elif grade == 'F' or grade == 'f':
					grade = 'incomplete'
				
				else:
					print('ogiltigt betyg, ange P eller F')
					continue
			
			elif t == 'points':
				try:
					grade = int(grade)
				
					if grade < 0:
						print('ogiltigt betyg, försök igen')
						continue
					
					grade = str(grade)
			
				except:
					print('ogiltigt betyg, försök igen')
					continue
			
			elif t == 'letter_grade':
				valid_grade = None
				
				for x in assignment['grading_scheme']:
					if x.casefold() == grade.casefold():
						valid_grade = x
						break
				
				if valid_grade is None:
					print('ogiltigt betyg, försök igen')
					continue
				
				grade = valid_grade
		
		result = put('/courses/' + str(course) + '/assignments/' + str(assignment['id']) + '/submissions/' + str(student['id']), { 'submission[posted_grade]': grade })
		
		if 'grade' not in result:
			print('fel från Canvas:')
			print(result)
			return True
		
		print('betyg ' + nice_grade(result['grade']) + ' för ' + nice_student(student) + ' är nu sparat')
		return True


while True:
	print('\nsök efter en student:')
	search_term = input('>> ')

	if len(search_term) == 0:
		break
	
	if len(search_term) < 3:
		print('sökordet måste ha minst tre tecken')
		continue

	students = get_list('/courses/' + str(course) + '/users?enrollment_type[]=student&search_term=' + search_term)

	if 'errors' in students:
		print('fel från Canvas:')
		for error in students['errors']:
			print(error['message'])
		continue

	elif len(students) == 0:
		print('hittade inga studenter')
		continue

	elif len(students) == 1:
		student = students[0]
	
	else:
		print('\nvälj en student (1 .. ' + str(len(students)) + '):')
		
		i = 1
		for s in students:
			print(str(i) + '\t' + nice_student(s))
			i += 1
		
		student = None
		
		while True:
			index = input('>> ')
			
			if len(index) == 0:
				break
			
			else:
				try:
					index = int(index)
					
					if index < 1 or index > len(students):
						print('ogiligt val, försök igen')
						continue
						
					student = students[index - 1]
					break
				
				except:
					print('ogiltigt val, försök igen')
					continue
	
	if student is None: continue
	
	choose_assignment(student)
