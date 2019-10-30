#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, dateutil.parser, threading
from canvas import Course, Assignment, Student, get_courses, get_list, put, nice_grade

# TODO, dateutil och request finns inte förinstallerat på alla system.

# requests at
# http://docs.python-requests.org/en/master/

###############################################################################
#
# GLOBAL VARIABLES
#

g_oldgrades = {} # global variable for coloring grades this session 
g_newgrades= {} # maintains input order of grades
g_color = True   # TODO göra optional, kolla färgändring fungerar på alla plattformar


lock = threading.Lock()


def thread_find_students_in_course(course, search_term, students):
	course_students = get_list('/courses/' + str(course.id) + '/users?enrollment_type[]=student&search_term=' + search_term)
	
	if 'errors' in course_students:
		print('fel från Canvas:')
		print(error)
		sys.exit(1)
	
	lock.acquire()
	for course_student in course_students:
		if course_student['id'] not in students:
			students[course_student['id']] = Student(course_student)
		
		students[course_student['id']].courses.append(course)
	lock.release()


def thread_retrieve_results_in_course(student, course):
	student.get_results(course)


def thread_retrieve_assignments(course, assignments):
	a = course.get_assignments()
	
	lock.acquire()
	for assignment in a: assignments.append(assignment)
	lock.release()


###############################################################################
#
# choose_assignment
#
def choose_assignment(student):
	fetch_grades = True
	
	while True:
		auto_choice = -1
		
		assignments = []
		threads = []
		
		for course in student.courses:
			threads.append(threading.Thread(target=thread_retrieve_assignments, args=(course, assignments)))
		
		for thread in threads: thread.start()
		for thread in threads: thread.join()
		
		assignments.sort()
		
		for i, assignment in enumerate(assignments, 1):
			if auto_choice == -1: auto_choice = i
			else: auto_choice = None
		
		if auto_choice is not None and auto_choice != -1:
			assignment_choice = assignments[auto_choice - 1]
			auto_choice = True
			
			print()
			print('nuvarande resultat för ' + assignment_choice['name'] + ': ', end = '')
			
			if assignment_choice['id'] in current_grades:
				current_grade = nice_grade(current_grades[assignment_choice['id']]['grade'])
				
				current_grade_date = current_grades[assignment_choice['id']]['date']
				current_grade_date = dateutil.parser.parse(current_grade_date).strftime('%Y-%m-%d %H:%M')
				
				print(current_grade + ' (' + current_grade_date + ')')
			
			else:
				print('-')
		
		else:
			auto_choice = False
			
			multiple_courses = len(courses) > 1
			padding = '\t' if multiple_courses else ''
			previous_course = None
			
			threads = []
			
			for course in student.courses:
				threads.append(threading.Thread(target=thread_retrieve_results_in_course, args=(student, course)))
			
			for thread in threads: thread.start()
			for thread in threads: thread.join()
			
			print('\nvälj uppgift för ' + str(student) + ':')
			print(padding + 'index  resultat  datum             uppgift')
			
			for i, assignment in enumerate(assignments, 1):
				if multiple_courses and previous_course != assignment.course:
					print('\n' + str(assignment.course))
					previous_course = assignment.course
				
				current_result = student.get_result(assignment)
				
				current_grade = nice_grade(current_result['grade'])
				current_grade_date = current_result['date']
				
				if current_grade_date is not None: current_grade_date = dateutil.parser.parse(current_grade_date).strftime('%Y-%m-%d %H:%M')
				else: current_grade_date = '                '
				
				print(padding, end = '')
				
				print('{0: <6}'.format(str(i)), end = ' ')
				entry = (student, assignment)
				isincolor = g_color and entry in g_oldgrades and g_oldgrades[ entry ] != current_grade
				if isincolor: print('\033[0;7m', end = '')
				print('{0: <10}'.format(current_grade), end = '')
				print(current_grade_date + '  ', end = '')
				if isincolor: print('\033[0m', end = '')
				
				print(assignment)
			
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
					if assignment.name.casefold() == choice.casefold():
						if assignment_choice is not None:
							print('flera uppgifter har samma namn, ange ett index')
							assignment_choice = -1
							break
						
						assignment_choice = assignment
				
				if assignment_choice is None:
					print('ogiltigt val, försök igen')
					continue
				
				if assignment_choice == -1:
					continue
		
		old_grade = nice_grade(student.get_result(assignment_choice)['grade'])
		fetch_grades = set_grade(student, assignment_choice, old_grade)
		
		if auto_choice: break


###############################################################################
#
# set_grade
#
def set_grade(student, assignment, old_grade):
	while True:
		print()
		
		if assignment.grades_affect_group: print('VARNING: detta är en gruppuppgift där alla i gruppen får samma resultat')
		if assignment.grading_type == 'letter_grade' and assignment.grading_scheme is None: print('VARNING: uppgiften borde ha en graderad betygsskala, men det verkar den inte ha')
		
		if len(courses) == 1: print('ange nytt resultat för \'' + str(student) + '\' på \'' + str(assignment) + '\'', end = ' ')
		else: print('ange nytt resultat för \'' + str(student) + '\' på \'' + str(assignment) + '\' i \'' + str(assignment.course) + '\'', end = ' ')
		
		if assignment.grading_type == 'pass_fail': print('(P, F, -):')
		elif assignment.grading_type == 'points': print('(0 .. , -):')
		elif assignment.grading_type == 'letter_grade' and assignment.grading_scheme is not None: print('(' + (', '.join(assignment.grading_scheme)) + ', -):')
		elif assignment.grading_type == 'letter_grade' and assignment.grading_scheme is None: print('(...okänd betygsskala..., -):')
		
		print('nuvarande resultat: ' + old_grade)
		
		grade = input('>> ')
		
		if len(grade) == 0:
			print('avbryter')
			return
		
		if grade == '-':
			grade = ''
		
		else:
			if assignment.grading_type == 'pass_fail':
				if grade == 'P' or grade == 'p':
					grade = 'complete'
				
				elif grade == 'F' or grade == 'f':
					grade = 'incomplete'
				
				else:
					print('ogiltigt resultat, ange P eller F')
					continue
			
			elif assignment.grading_type == 'points':
				try:
					grade = int(grade)
				
					if grade < 0:
						print('ogiltigt resultat, försök igen')
						continue
					
					grade = str(grade)
			
				except:
					print('ogiltigt resultat, försök igen')
					continue
			
			elif assignment.grading_type == 'letter_grade' and assignment.grading_scheme is not None:
				valid_grade = None
				
				for x in assignment.grading_scheme:
					if x.casefold() == grade.casefold():
						valid_grade = x
						break
				
				if valid_grade is None:
					print('ogiltigt resultat, försök igen')
					continue
				
				grade = valid_grade

		result = put('/courses/' + str(assignment.course.id) + '/assignments/' + str(assignment.id) + '/submissions/' + str(student.id), { 'submission[posted_grade]': grade })
		
		# tvinga omladdning av studentens alla resultat för aktuell kurs från Canvas in till vår lokala cache
		student.get_results(assignment.course, True)
		
		if 'grade' not in result:
			print('fel från Canvas:')
			print(result)
			return
		
		print('resultat ' + nice_grade(result['grade']) + ' för ' + str(student) + ' är nu sparat')
		
		entry = (student, assignment)
		if not entry in g_oldgrades: g_oldgrades[entry] = old_grade
		
		g_newgrades[entry] = nice_grade(grade)
		
		return

###############################################################################
#
# entrylist
# 
def entrylist():
	print('införda resultat i Canvas:')
	changes = False
	
	for entry in g_newgrades:
		(student, assignment) = entry
		
		newgrade = g_newgrades[entry]
		oldgrade = g_oldgrades[entry]
		
		if newgrade != oldgrade:
			print('  {0: <30} {1: <3} {3} ({2}) '.format(str(student), newgrade, oldgrade, str(assignment)) )
			changes = True
	
	if not changes: print('  inga resultat införda')


###############################################################################
#
# run_instructions
# 
def run_instructions():
	print('kör så här: enstaka.py <kursnamn>')
	sys.exit(1)
      # TODO help text

###############################################################################
#
# parse_commandline_options
# 
def parse_commandline_options():
	global g_color
	for arg in sys.argv:
		if arg == "--nocolor":
			g_color = False

###############################################################################
#
# main
#
if len(sys.argv) < 2:
	run_instructions()
	sys.exit(1)


parse_commandline_options()

courses = get_courses(sys.argv[1])

if len(courses) == 0:
	print('hittade ej angiven kurs')
	sys.exit(1)


courses.sort(key = lambda x: x.date_start + x.name)


print('resultat för:')

for course in courses:
	print('\t' + str(course))

while True:
	print('\nsök efter en student:')
	search_term = input('>> ')

	if len(search_term) == 0:
		break
	
	if len(search_term) < 3:
		print('sökordet måste ha minst tre tecken')
		continue
	
	students = {}
	threads = []
	
	for course in courses:
		threads.append(threading.Thread(target=thread_find_students_in_course, args=(course, search_term, students)))
	
	for thread in threads: thread.start()
	for thread in threads: thread.join()
	
	students = [students[key] for key in students]
	
	sorted(students)
	
	if len(students) == 0:
		print('hittade inga studenter')
		continue
	
	elif len(students) == 1:
		chosen_student = students[0]
	
	else:
		print('\nvälj en student (1 .. ' + str(len(students)) + '):')
		
		students.sort()
		
		i = 1
		for student in students:
			print(str(i) + '\t' + str(student))
			
			# skriv ut vilka kurser studenten går i om vi söker i flera kurser
			if len(courses) > 1: print('\t' + (', '.join([str(course) for course in student.courses])) + '\n')
			
			i += 1
		
		chosen_student = None
		
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
						
					chosen_student = students[index - 1]
					break
				
				except:
					print('ogiltigt val, försök igen')
					continue
	
	if chosen_student is None: continue
	
	choose_assignment(chosen_student)

entrylist()
