#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from canvas import get_list, get_object, put, post

if len(sys.argv) != 2:
	print('kör så här: rappkorrigering.py <kurs-ID>')
	sys.exit(1)


try:
	canvas_id = int(sys.argv[1])

except:
	print('ogiltigt kurs-ID')
	sys.exit(1)


course = next(({
	'id': course['id'],
	'name': course['name'],
	'sis': course['sis_course_id']
} for course in get_list('/courses') if len([x for x in course['enrollments'] if x['type'] != 'student']) > 0 and course['id'] == canvas_id), None)

if course is None:
	print('hittade inte kursen')
	sys.exit(1)


if not course['sis'].startswith('RAPP_'):
	print('verkar ej vara en Rapp-importerad kurs')
	sys.exit(1)


existing_grading_standards = get_list('/courses/' + str(course['id']) + '/grading_standards')

default_grades = {
	'A': 0.9,
	'B': 0.8,
	'C': 0.7,
	'D': 0.6,
	'E': 0.5,
	'VG': 0.4,
	'G': 0.3,
	'P': 0.2,
	'Fx': 0.1,
	'F': 0
}

# hitta uppgifter som har felaktiga betygsskalor
assignments = get_list('/courses/' + str(course['id']) + '/assignments')

assignment_grading_standards = {}
assignments_to_handle = []

for assignment in assignments:
	if assignment['grading_standard_id'] is not None:
		if 'grading_standard_id' not in assignment_grading_standards:
			grading_standard = next((x for x in existing_grading_standards if x['id'] == assignment['grading_standard_id']), None)
			
			assignment_grading_standards[assignment['grading_standard_id']] = grading_standard
			
		if assignment_grading_standards[assignment['grading_standard_id']] == None:
			assignments_to_handle.append(assignment)


if len(assignments_to_handle) == 0:
	print('inga uppgifter att korrigera')
	sys.exit(0)


# kontrollera vilka betyg studenterna har fått på de uppgifter som har felaktiga betygsskalor
for assignment in assignments_to_handle:
	submissions = get_list('/courses/' + str(course['id']) + '/assignments/' + str(assignment['id']) + '/submissions')
	
	grades = list(set(x['grade'] for x in submissions if x['grade'] is not None))
	
	for grade in grades:
		if grade not in default_grades:
			print('okänt betyg ' + grade)
			sys.exit(1)


# har vi någon betygsskala i kursen som precis täcker in de vi söker (A-F, Fx, VG, G och P)?
default_grading_standard = None

for existing_grading_standard in existing_grading_standards:
	grades = [x['name'] for x in existing_grading_standard['grading_scheme']].sort()
	
	if grades == list(default_grades.keys()).sort():
		default_grading_standard = existing_grading_standard['id']
		break


# om inte, skapa en
if default_grading_standard is None or True is True:
	post_string = 'title=betygsskala'
	
	grades = list(default_grades.keys())
	grades.sort(key = lambda x: default_grades[x], reverse = True)
	
	for grade in grades:
		post_string += '&grading_scheme_entry[][name]=' + grade + '&grading_scheme_entry[][value]=' + str(default_grades[grade])
	
	grading_standard = post('/courses/' + str(course['id']) + '/grading_standards', post_string)
	
	if 'id' not in grading_standard:
		print('kunde inte skapa betygsskala')
		sys.exit(1)
	
	default_grading_standard = grading_standard['id']


# se till så att de berörda uppgifterna får en korrekt betygsskala
assignments_to_handle_ids = [x['id'] for x in assignments_to_handle]

for assignment in assignments:
	if assignment['id'] in assignments_to_handle_ids:
		result = put('/courses/' + str(course['id']) + '/assignments/' + str(assignment['id']), {
			'assignment[grading_standard_id]': default_grading_standard
		})
	
		print('korrigerar uppgift \'' + assignment['name'] + '\'', end = '...')
	
		if 'grading_standard_id' not in result or result['grading_standard_id'] != default_grading_standard:
			print(' MISSLYCKADES')
			sys.exit(1)
	
		else:
			print(' OK')
	
	else:
		print('hoppar över uppgift \'' + assignment['name'] + '\'')
