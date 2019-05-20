# -*- coding: utf-8 -*-

# Den här filen innehåller hjälpfunktioner som används av skripten.

import requests, sys, re, dateutil.parser

g_base = 'https://kth.instructure.com/api/v1'
g_grading_schemes = {}
g_access_token = -1


try:
	fh = open('hemlig-nyckel.txt', 'r')
	g_access_token = fh.read().strip()
	fh.close()

except:
	print('misslyckades med att läsa in den hemliga nyckeln')
	print('generera med nyckelskapare.py')
	sys.exit(1)


class Course:
	def __init__(self, course):
		self.id = course['id']
		self.name = course['name']
		self.name_original = course['original_name'] if 'original_name' in course else None
		self.code = course['course_code'][0:6]
		self.date_start = course['start_at'][0:10]
		self.__assignments = None
		self.__students = None
	
	def get_students(self):
		if self.__students is None:
			course_students = get_list('/courses/' + str(self.id) + '/users?enrollment_type[]=student')
			
			self.__students = [Student(course_student) for course_student in course_students]
		
		return self.__students
	
	def get_assignments(self):
		if self.__assignments is None:
			assignments = get_list('/courses/' + str(self.id) + '/assignments')
			
			if 'errors' in assignments:
				print('fel vid inläsning av uppgifter -- kanske fel API-nyckel eller fel kurs-ID?')
				print(assignments['errors'])
				sys.exit(1)
			
			self.__assignments = []
			
			for assignment in assignments:
				if not assignment['published']: continue
				if assignment['grading_type'] not in ['pass_fail', 'points', 'letter_grade']: continue
				
				if assignment['grading_standard_id'] is not None: grading_scheme = self.get_grading_scheme(assignment['grading_standard_id'])
				else: grading_scheme = None
				
				grades_affect_group = not assignment['grade_group_students_individually'] and assignment['group_category_id'] is not None
				
				self.__assignments.append(Assignment(self, assignment['id'], assignment['name'], assignment['grading_type'], grading_scheme, grades_affect_group))
		
		return self.__assignments
	
	def get_grading_scheme(self, id):
		global g_grading_schemes
		
		if id not in g_grading_schemes:
			grading_standard = get_object('/courses/' + str(self.id) + '/grading_standards/' + str(id))
			g_grading_schemes[id] = [grade['name'] for grade in grading_standard['grading_scheme']] if 'grading_scheme' in grading_standard else None
		
		return g_grading_schemes[id]
	
	def __contains__(self, key):
		return key in self.name or key in self.code
	
	def __str__(self):
		return self.name


class Assignment():
	def __init__(self, course, id, name, grading_type, grading_scheme, grades_affect_group):
		self.course = course
		self.id = id
		self.name = name
		self.grading_type = grading_type
		self.grading_scheme = grading_scheme
		self.grades_affect_group = grades_affect_group
	
	def __str__(self):
		return self.name


class Student:
	def __init__(self, student):
		self.id = student['id']
		self.name = student['name']
		self.email_address = student['login_id'] if 'login_id' in student else None
		self.courses = []
		self.__results = {}
	
	def get_results(self, course, force_upgrade = False):
		if course in self.__results and not force_upgrade: return self.__results[course]
		
		submissions = get_list('/courses/' + str(course.id) + '/students/submissions?student_ids[]=' + str(self.id))
		
		self.__results[course] = {}
		
		for submission in submissions:
			assignment = next(x for x in course.get_assignments() if x.id == submission['assignment_id'])
			
			if submission['grade'] is None: continue
			
			self.__results[course][assignment] = {
				'grade': submission['grade'],
				'date': submission['graded_at']
			};
		
		return self.__results[course]
	
	def get_result(self, assignment, force_upgrade = False):
		current_grades = self.get_results(assignment.course, force_upgrade = force_upgrade)
		return current_grades[assignment] if assignment in current_grades else {'grade': '-', 'date': None}
	
	def __str__(self):
		return (self.name + ' <' + self.email_address + '>') if self.email_address is not None else self.name
	
	def __lt__(self, other):
		return self.name < other.name


# När man hämtar listor från Canvas får man inte alltid alla element, utan bara
# de på den första "sidan". Den här funktionen hämtar början av en lista och går
# igen resten av sidorna ända till den har nått slutet. Resultatet sätts ihop
# i en slutgiltig lista, så att svaret man får är hela listan.
def get_list(url):
	response = []
	
	while url is not None:
		if not url.startswith(g_base): url = g_base + url
		
		if '?' in url: url = url.replace('?', '?per_page=100&')
		else: url += '?per_page=100'
		
		response_this = requests.get(url = url, headers = { 'Authorization': 'Bearer ' + g_access_token })
		response_list = response_this.json()
		
		if type(response_list) is not list: return response_list
		
		response += response_list
	
		url = None
	
		if 'Link' in response_this.headers:
			r = re.search('<([^>]+?)>; rel="next"', response_this.headers['Link'])
		
			if r is not None: url = r.group(1)
		
	return response


def get_object(url):
	return requests.get(url = g_base + url, headers = { 'Authorization': 'Bearer ' + g_access_token }).json()


def put(url, data):
	return requests.put(url = g_base + url, headers = { 'Authorization': 'Bearer ' + g_access_token }, data = data).json()


def post(url, data):
	return requests.post(url = g_base + url, headers = { 'Authorization': 'Bearer ' + g_access_token }, data = data).json()


def delete(url):
	return requests.delete(url = g_base + url, headers = { 'Authorization': 'Bearer ' + g_access_token }).json()


# Hittar kurser som användaren har någon annan roll än student i. Om en sökterm
# anges returneras endast de kurser som någonstans i namnet eller kurskoden
# matchar den söktermen.
def get_courses(search_term = None):
	all_courses = [Course(course) for course in get_list('/courses') if len([x for x in course['enrollments'] if x['type'] != 'student']) > 0]
	
	return all_courses if search_term is None else [course for course in all_courses if search_term in course]


def nice_grade(grade):
	if grade is None: return '-'
	
	grade = str(grade)
	
	if grade == '' : return '-'
	if grade == 'incomplete': return 'F'
	if grade == 'complete': return 'P'
	
	return grade
