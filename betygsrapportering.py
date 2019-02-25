#!/usr/bin/python3
from config import access_token, courses
import requests, json, sys

base = 'https://kth.instructure.com/api/v1'


if len(sys.argv) != 2:
	print('kör så här: betygsrapportering.py <kursnamn>')
	sys.exit(1)

if sys.argv[1] not in courses:
	print('hittade ej angiven kurs')
	sys.exit(1)

course = courses[sys.argv[1]]


assignments = requests.get(url = base + '/courses/' + str(course) + '/assignments?access_token=' + access_token).json()
assignments = [assignment for assignment in assignments if assignment['published'] and (assignment['grading_type'] == 'pass_fail' or assignment['grading_type'] == 'points')]

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
	while True:
		print('\nvälj uppgift för ' + nice_student(student) + ':')
	
		i = 1
		for assignment in assignments:
			print(str(i) + '\t' + assignment['name'])
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
	
		set_grade(student, assignment_choice)


def set_grade(student, assignment):
	if assignment['grading_type'] == 'pass_fail' or assignment['grading_type'] == 'points': t = assignment['grading_type']
	else: raise Exception
	
	while True:
		print()
		
		if t == 'pass_fail': print('skriv in betyget (P, F, -):')
		elif t == 'points': print('skriv in betyget (0 .. , -):')
		
		grade = input('>> ')
		
		if len(grade) == 0:
			print('avbryter')
			return
		
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
		
		result = requests.put(url = base + '/courses/' + str(course) + '/assignments/' + str(assignment['id']) + '/submissions/' + str(student['id']) + '?access_token=' + access_token, data = { 'submission[posted_grade]': grade }).json()
		
		if 'grade' not in result:
			print('fel från Canvas:')
			print(result)
			break
		
		print('betyg ' + nice_grade(result['grade']) + ' för ' + nice_student(student) + ' är nu sparat')
		break


while True:
	print('\nsök efter en student:')
	search_term = input('>> ')

	if len(search_term) == 0:
		break
	
	if len(search_term) < 3:
		print('sökordet måste ha minst tre tecken')
		continue

	students = requests.get(url = base + '/courses/' + str(course) + '/users?enrollment_type[]=student&search_term=' + search_term + '&access_token=' + access_token).json()

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
