#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, openpyxl, datetime, re
from collections import defaultdict
from canvas import get_courses, get_list, get_object, post, nice_grade


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
	
	assignments_with_points = set([a.id for a in assignments if a.grading_type == 'points'])
	
	print('läser in studenter...')
	students = course.get_students()
	
	if include_grades:
		print('läser in resultat...')
		results = get_list('/courses/' + str(course.id) + '/students/submissions?student_ids[]=all')
		
		grades = defaultdict(lambda: defaultdict(lambda: None))
		
		for result in [x for x in results if x['grade'] is not None]:
			grades[result['user_id']][result['assignment_id']] = nice_grade(result['grade'], False)
	
	else:
		grades = None
	
	print()
	
	return (assignments, assignments_with_points, students, grades)


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
	
	(assignments, assignments_with_points, students, grades) = read_cache(course)
	
	if file_name == '-':
		now = datetime.datetime.now()
		file_name = 'resultatutdrag_' + course.code + '_' + now.strftime('%Y-%m-%d') + '_' + now.strftime('%H%M%S') + '.xlsx'
	
	if not file_name.endswith('.xlsx'): file_name += '.xlsx'
	
	wb = openpyxl.Workbook()
	ws = wb.active
	
	header = ['namn', 'e-postadress', 'ID'] + [a.name + ' (' + str(a.id) + ')' for a in assignments]
	ws.append(header)
	
	for student in students:
		row = [student.name, student.email_address, student.id] + [int(grades[student.id][a.id]) if a.id in assignments_with_points and grades[student.id][a.id] is not None else grades[student.id][a.id] for a in assignments]
		ws.append(row)
	
	wb.save(file_name)
	
	print('fil \'' + file_name + '\' sparad')


if argc == 3:
	try:
		wb = openpyxl.load_workbook(sys.argv[2])

	except:
		print('kunde ej öppna angiven fil')
		sys.exit(1)
	
	
	if len(wb.sheetnames) != 1:
		print('kalkylbladet måste ha precis ett blad, hittade ' + str(len(wb.sheetnames)))
		sys.exit(1)
	
	(assignments, assignments_with_points, students, grades) = read_cache(course)
	
	ws = wb.active
	
	student_ids = set([x.id for x in students])
	
	student_column = None
	columns = {}

	for cell in ws[1]:
		if cell.value is None: continue
		
		if cell.value == 'ID':
			if student_column is not None:
				print('det finns flera kolumner med ID')
				sys.exit(1)
			
			student_column = cell.column - 1
		
		else:
			assignment_id = re.search('\(([0-9]+)\)$', cell.value)
			
			if assignment_id is not None:
				assignment_id = int(assignment_id.group(1))
				assignment = next((x for x in assignments if x.id == assignment_id), None)
				
				if assignment is None:
					print('okänd uppgift ' + str(assignment_id))
					sys.exit(1)
				
				if assignment in columns.values():
					print('det finns flera kolumner som avser uppgift ' + str(assignment_id))
					sys.exit(1)
				
				columns[cell.column - 1] = assignment
	
	
	# läs in betyg från kalkylbladet
	file_grades = defaultdict(lambda: defaultdict(lambda: None))
	
	for cell in ws['A']:
		if cell.row == 1: continue
		
		student_id = ws[cell.row][student_column].value
		
		if not isinstance(student_id, int):
			print('rad ' + str(cell.row) + ' ignoreras eftersom den saknar student-ID')
			continue
		
		if student_id in file_grades:
			print('rad ' + str(cell.row) + ' har en student som har förekommit på en tidigare rad')
			sys.exit(1)
		
		if student_id not in student_ids:
			print('rad ' + str(cell.row) + ' har en student som inte hittades i kursen')
			sys.exit(1)
		
		for assignment_column in columns:
			grade = ws[cell.row][assignment_column].value
			
			if grade is None: continue
			if isinstance(grade, int): grade = str(grade)
			
			file_grades[student_id][columns[assignment_column].id] = grade
	
	wb.close()
	
	
	# hitta differensen
	difference = defaultdict(lambda: defaultdict(lambda: None))
	
	for s in grades:
		for a in columns.values():
			a = a.id
			
			grade_canvas = grades[s][a]
			grade_file = file_grades[s][a]
			
			if grade_canvas is None: grade_canvas = '-'
			if grade_file is None: continue
			
			if grade_canvas != grade_file:
				difference[s][a] = (grade_canvas, file_grades[s][a])
	
	for s in file_grades:
		for a in columns.values():
			a = a.id
			
			grade_canvas = grades[s][a]
			grade_file = file_grades[s][a]
			
			if grade_canvas is None: grade_canvas = '-'
			if grade_file is None: continue
			
			if grade_canvas != grade_file:
				difference[s][a] = (grade_canvas, file_grades[s][a])
	
	if len(difference) == 0:
		print('ingen skillnad mellan kalkylbladet och Canvas')
		sys.exit(1)
	
	
	touched_assignments = []
	
	print('antal resultat  uppgift')
	
	for assignment in assignments:
		if assignment not in columns.values():
			changes = '-'
		
		else:
			changes = 0
			
			for s in difference:
				if assignment.id in difference[s]: changes += 1
		
			if changes != 0: touched_assignments.append(assignment)
		
		print('{0: >14}'.format(str(changes)), end = '  ')
		print(str(assignment))
	
	
	wb = openpyxl.Workbook()
	ws = wb.active
	
	header = ['namn', 'e-postadress', 'ID']
	
	for a in touched_assignments:
		header.append('')
		header.append(a.name + ' (i Canvas)')
		header.append(a.name + ' (' + str(a.id) + ')')
	
	ws.append(header)
	
	for s in students:
		if s.id not in difference: continue
		row = [s.name, s.email_address, s.id]
		
		for a in touched_assignments:
			row.append('')
			
			c = difference[s.id][a.id]
			
			if c is None:
				row.append('')
				row.append('')
			
			else:
				row.append(c[0])
				row.append(c[1])
		
		ws.append(row)
	
	print()
	
	assignments_dict = {}
	for a in assignments: assignments_dict[a.id] = a
	
	error = False
	
	for s in difference:
		for a in difference[s]:
			grade = grade2api(difference[s][a][1], assignments_dict[a])
			
			if grade is None:
				student = next(x for x in students if x.id == s)
				print('felaktigt resultat \'' + difference[s][a][1] + '\' för \'' + str(student) + '\' på \'' + str(assignment) + '\'')
				error = True
			
			difference[s][a] = grade
	
	if error: sys.exit(1)
	
	try:
		wb.save('skillnad.xlsx')
		print('skillnaden har sparats i skillnad.xlsx -- skriv \'OK\' för att rapportera in resultaten')
	
	except:
		print('skillnaden kunde inte sparas till skillnad.xlsx -- skriv \'OK\' för att rapportera in resultaten ändå')
	
	command = input('>> ')

	if command.lower() != 'ok':
		print('avbryter och avslutar')
		sys.exit(1)

	for a in assignments:
		data = {}
		
		for s in difference:
			grade = difference[s][a.id]
			
			if grade is None: continue
			
			data['grade_data[' + str(s) + '][posted_grade]'] = grade
		
		if len(data) == 0: continue
		
		print('skriver ' + str(len(data)) + ' resultat för \'' + str(a) + '\'')
		
		result = post('/courses/' + str(course.id) + '/assignments/' + str(a.id) + '/submissions/update_grades', data)
		
		if 'errors' in result:
			print('fel från Canvas:')
			print(result)
