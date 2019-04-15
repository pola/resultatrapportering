#!/usr/bin/python3
# -*- coding: utf-8 -*-
from canvascourses import courses
import requests, json, sys, re, dateutil.parser

try:
	fh = open('hemlig-nyckel.txt', 'r')
	access_token = fh.read().strip()
	fh.close()

except:
	print('misslyckades med att läsa in den hemliga nyckeln')
	print('generera med nyckelskapare.py')
	sys.exit(1)

# TODO, dateutil och request finns inte förinstallerat på alla system.

# requests at
# http://docs.python-requests.org/en/master/

###############################################################################
#
# GLOBAL VARIABLES
#

g_base = 'https://kth.instructure.com/api/v1'
g_oldgrades = {} # global variable for coloring grades this session 
g_newgrades= {} # maintains input order of grades
g_color = True   # TODO göra optional, kolla färgändring fungerar på alla plattformar
g_lowerlimit = 0     # limit number of assignment to show
g_upperlimit = 1000000

###############################################################################
#
# get_list
#
def get_list(url):
	response = []
	
	while url is not None:
		if not url.startswith(g_base): url = g_base + url
		
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


###############################################################################
#
# get_object
#
def get_object(url):
	return requests.get(url = g_base + url, headers = { 'Authorization': 'Bearer ' + access_token }).json()


###############################################################################
#
# put
#
def put(url, data):
	return requests.put(url = g_base + url, headers = { 'Authorization': 'Bearer ' + access_token }, data = data).json()


###############################################################################
#
# nice_student
#
def nice_student(student):
	return (student['short_name'] + ' <' + student['email'] + '>') if 'email' in student else student['short_name']


###############################################################################
#
# nice_grade
#
def nice_grade(grade):
	if grade is None: return '-'
	
	grade = str(grade)
	
	if grade == '' : return '-'
	if grade == 'incomplete': return 'F'
	if grade == 'complete': return 'P'
	
	return grade


###############################################################################
#
# choose_assignment
#
def choose_assignment(student, course, assignments):
	global g_lowerlimit
	global g_upperlimit
	fetch_grades = True
	
	while True:
		if fetch_grades:
			current_grades = {}
			submissions = get_list('/courses/' + str(course) + '/students/submissions?student_ids[]=' + str(student['id']))
	
			for submission in submissions:
				current_grades[submission['assignment_id']] = {
					'grade': submission['grade'],
					'date': submission['graded_at']
				}
		
		auto_choice = -1
		
		for i, assignment in enumerate(assignments, 1):
			if i < g_lowerlimit: continue
			if i > g_upperlimit: continue
			
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
			
			print('\nvälj uppgift för ' + nice_student(student) + ':')
			print('index  resultat  datum             uppgift')
		
			for i, assignment in enumerate(assignments, 1):
				if i < g_lowerlimit: continue
				if i > g_upperlimit: continue
				
				current_grade = nice_grade(current_grades[assignment['id']]['grade']) if assignment['id'] in current_grades else '-'
				current_grade_date = current_grades[assignment['id']]['date']
				
				if current_grade_date is not None: current_grade_date = dateutil.parser.parse(current_grade_date).strftime('%Y-%m-%d %H:%M')
				else: current_grade_date = '                '
				
				print('{0: <6}'.format(str(i)), end = ' ')
				entry = ( student['id'], student['short_name'], assignment['name'] )
				isincolor = g_color and entry in g_oldgrades and g_oldgrades[ entry ] != current_grade
				if isincolor: print('\033[0;7m', end='')
				print('{0: <10}'.format(current_grade), end = '')
				print(current_grade_date + '  ', end = '')
				if isincolor: print('\033[0m', end='')
				
				print(assignment['name'])
			
			choice = input('>> ')
			
			if len(choice) == 0:
				return

			# TODO special choices ?
			if choice == '?':
				print("TODO: call help function")
				continue

			# Limit assignements to show
			m = re.search('>(\d\d?)$', choice)
			if m:
				g_lowerlimit = int(m.group(1))
				continue
			
			m = re.search('<(\d\d?)$', choice)
			if m:
				g_upperlimit = int(m.group(1))
				continue
			
			try:
				choice = int(choice)
			
				if choice < 1 or choice > len(assignments):
					print('ogiltigt val, försök igen')
					continue
			
				assignment_choice = assignments[choice - 1]
		
			except:
				assignment_choice = None
			
				for assignment in assignments:
					if assignment['name'].casefold() == choice.casefold():
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

		old_grade = nice_grade(current_grades[assignment_choice['id']]['grade']) if assignment_choice['id'] in current_grades else '-'
		fetch_grades = set_grade(student, assignment_choice, old_grade)
		
		if auto_choice: break


###############################################################################
#
# set_grade
#
def set_grade(student, assignment, old_grade):
	if assignment['grading_type'] == 'pass_fail' or assignment['grading_type'] == 'points' or assignment['grading_type'] == 'letter_grade':
                t = assignment['grading_type']
	else:
                raise Exception

	while True:
		print()
		
		if not assignment['grade_group_students_individually'] and assignment['group_category_id'] is not None:
			print('VARNING: detta är en gruppuppgift där alla i gruppen får samma resultat')
		
		print('ange resultat för ' + nice_student(student) + ' på ' + assignment['name'] + ' ', end = '')
		
		if t == 'pass_fail': print('(P, F, -):')
		elif t == 'points': print('(0 .. , -):')
		elif t == 'letter_grade': print('(' + (', '.join(assignment['grading_scheme'])) + ', -):')
		
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
					print('ogiltigt resultat, ange P eller F')
					continue
			
			elif t == 'points':
				try:
					grade = int(grade)
				
					if grade < 0:
						print('ogiltigt resultat, försök igen')
						continue
					
					grade = str(grade)
			
				except:
					print('ogiltigt resultat, försök igen')
					continue
			
			elif t == 'letter_grade':
				valid_grade = None
				
				for x in assignment['grading_scheme']:
					if x.casefold() == grade.casefold():
						valid_grade = x
						break
				
				if valid_grade is None:
					print('ogiltigt resultat, försök igen')
					continue
				
				grade = valid_grade

		result = put('/courses/' + str(course) + '/assignments/' + str(assignment['id']) + '/submissions/' + str(student['id']), { 'submission[posted_grade]': grade })
		if 'grade' not in result:
			print('fel från Canvas:')
			print(result)
			return True     # TODO ???
		
		print('resultat ' + nice_grade(result['grade']) + ' för ' + nice_student(student) + ' är nu sparat')

		entry = ( student['id'], student['short_name'], assignment['name'] )
		if not entry in g_oldgrades:
			g_oldgrades[entry] = old_grade
		g_newgrades[entry] = nice_grade(grade)
		return True

###############################################################################
#
# entrylist
# 
def entrylist():
	print("Införda resultat i canvas:")
	changes = False
	for entry in g_newgrades:
		email    = entry[0]
		name     = entry[1]
		assignm  = entry[2]
		newgrade = g_newgrades[ entry ]
		oldgrade = g_oldgrades[ entry ]
		if newgrade != oldgrade :
			print('  {0: <30} {1: <3} {3} ({2}) '.format(name, newgrade, oldgrade, assignm) )
			changes = True
	if not changes:
		print("  inga resultat införda")
			
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
	global g_color, g_lowerlimit, g_upperlimit
	for arg in sys.argv:
		if arg == "--nocolor":
			g_color = False
		m = re.search('f(\d\d?)$', arg)
		if m:
			g_lowerlimit = int(m.group(1))
		m = re.search('t(\d\d?)$', arg)
		if m:
			g_upperlimit = int(m.group(1))

###############################################################################
#
# main
#
if __name__ == "__main__":
	if len(sys.argv) < 2:
		run_instructions()
		sys.exit(1)

	parse_commandline_options()

	kurs = sys.argv[1]
	if kurs not in courses:
		print('hittade inte kursen', kurs, 'i coursecanvas.py')
		sys.exit(1)
                
	course = courses[kurs]      # canvas course id
	
	assignments22 = get_list('/courses/' + str(course) + '/assignments')
	
	if 'errors' in assignments22:
		print('fel vid inläsning av uppgifter -- kanske fel API-nyckel eller fel kurs-ID?')
		print(assignments22['errors'])
		sys.exit(1)
	
	assignments22 = [assignment for assignment in assignments22 if assignment['published'] and (assignment['grading_type'] == 'pass_fail' or assignment['grading_type'] == 'points' or assignment['grading_type'] == 'letter_grade')]
	
	grading_standards = {}
	
	for assignment in assignments22:
		if assignment['grading_standard_id'] is not None:
			gsi = assignment['grading_standard_id']
			
			if gsi not in grading_standards:
				grading_standards[gsi] = [grade['name'] for grade in get_object('/courses/' + str(course) + '/grading_standards/' + str(gsi))['grading_scheme']]
			
			assignment['grading_scheme'] = grading_standards[gsi]
	
	if len(assignments22) == 0:
		print('hittade inga uppgifter')
		sys.exit(1)
	
	        
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
		
		choose_assignment(student, course, assignments22)
	entrylist()
