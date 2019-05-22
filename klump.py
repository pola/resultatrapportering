#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, openpyxl, datetime
from collections import defaultdict
from canvas import Course, Assignment, Student, get_courses, get_list, get_object, put, nice_grade
from pprint import pprint


def grade2api(grade, assignment):
	if grade == '-': return ''
	
	if assignment.grading_type == 'pass_fail':
		if grade == 'P' or grade == 'p': return 'complete'
		if grade == 'F' or grade == 'f': return 'incomplete'
		
		return None
	
	if assignment.grading_type == 'points':
		try:
			grade = int(grade)
			
			if grade < 0: return None
			
			return str(grade)
		
		except:
			return None
	
	if assignment.grading_type == 'letter_grade':
		if assignment.grading_scheme is None:
			return None
		
		else:
			valid_grade = None
			
			for x in assignment.grading_scheme:
				if x.casefold() == grade.casefold():
					valid_grade = x
					break
			
			return valid_grade
	
	else:
		return None


def read_cache(course, include_grades = True):
	print('läser in uppgifter...')
	assignments = course.get_assignments()
	
	print('läser in studenter...')
	students = course.get_students()
	
	if include_grades:
		print('läser in resultat...')
		results = get_list('/courses/' + str(course.id) + '/students/submissions?student_ids[]=all')
		
		assignments_with_points = set([a.id for a in assignments if a.grading_type == 'points'])
		
		grades = defaultdict(lambda: defaultdict(lambda: None))
		
		for result in [x for x in results if x['grade'] is not None]:
			grade = int(result['grade']) if result['assignment_id'] in assignments_with_points else result['grade']
			grades[result['user_id']][result['assignment_id']] = grade
	
	else:
		grades = None
	
	print()
	
	return (assignments, students, grades)


argc = len(sys.argv)

if argc != 2 and argc != 3:
	print('kör så här: klump.py <kursnamn> [<filnamn>]')
	sys.exit(1)


courses = get_courses(sys.argv[1])


if len(courses) == 0:
	print('hittade ej angiven kurs')
	sys.exit(1)


if len(courses) == 1:
	course = courses[0]

else:
	i = 1
	
	print('index  startdatum  kurskod  namn')
	
	for course in courses:
		print('{0: <6}'.format(str(i)), end = ' ')
		print(course.date_start, end = '  ')
		print(course.code, end = '   ')
		print(course.name)
		
		i += 1
	
	print()
	
	print('flera kurser hittades -- ange index för den kurs du vill hantera:')
	course_choice = input('>> ')
	
	print()
	
	try:
		course = courses[int(course_choice) - 1]
	
	except:
		print('ogiltigt val av kurs, avbryter')
		sys.exit(1)


if argc == 2:
	print('ange namn för exporterad fil, eller - för \'resultatutdrag_<kurskod>_<datum>_<klockslag>\':')
	file_name = input('>> ').strip()
	
	print()
	
	if len(file_name) == 0:
		print('inget filnamn angivet, avslutar')
		sys.exit(1)
	
	(assignments, students, grades) = read_cache(course)
	
	if file_name == '-':
		now = datetime.datetime.now()
		file_name = 'resultatutdrag_' + course.code + '_' + now.strftime('%Y-%m-%d') + '_' + now.strftime('%H%M%S') + '.xlsx'
	
	if not file_name.endswith('.xlsx'): file_name += '.xlsx'
	
	wb = openpyxl.Workbook()
	ws = wb.active
	
	header = ['namn', 'e-postadress', 'ID'] + [a.name + ' (' + str(a.id) + ')' for a in assignments]
	ws.append(header)
	
	for student in students:
		row = [student.name, student.email_address, student.id] + [grades[student.id][a.id] for a in assignments]
		ws.append(row)
	
	wb.save(file_name)
	
	print('fil \'' + file_name + '\' sparad')


if argc == 3:
	print('ej implementerat, avslutar')
	sys.exit(1)
	
	# TODO: läs från excel med https://openpyxl.readthedocs.io/en/stable/
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
