#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from canvas import get_access_token, get_list, put, delete


if get_access_token() is None:
	print('misslyckades med att läsa in den hemliga nyckeln')
	print('generera med nyckelskapare.py')
	sys.exit(1)


def set_nickname(course):
	if course['name_original'] is None:
		print('Namn:              ' + course['name_current'])
	
	else:
		print('Smeknamn:          ' + course['name_current'])
		print('Ursprungligt namn: ' + course['name_original'])
	
	print('Kurskod:           ' + course['code'])
	print('Startdatum:        ' + course['date_start'])
	
	print()
	
	if course['name_original'] is None: print('ange smeknamn:')
	else: print('ange nytt smeknamn, eller - för att rensa:')
	
	nickname = input('>> ')
	
	if len(nickname) == 0: print('avbryter')
	elif nickname == '-': delete('/users/self/course_nicknames/' + str(course['id']))
	else: put('/users/self/course_nicknames/' + str(course['id']), { 'nickname': nickname })
	
	print()



while True:
	courses = [{
		'id': course['id'],
		'name_current': course['name'],
		'name_original': course['original_name'] if 'original_name' in course else None,
		'code': course['course_code'][0:6],
		'date_start': course['start_at'][0:10],
	} for course in get_list('/courses') if len([x for x in course['enrollments'] if x['type'] != 'student']) > 0]
	
	courses.sort(key = lambda x: x['date_start'] + x['name_current'])
	
	if len(courses) == 0:
		print('misslyckades med att hämta kurser -- felaktig nyckel?')
		sys.exit(1)
	
	print('index  startdatum  kurskod  namn')
	
	i = 1
	last_year = None
	
	for course in courses:
		year = course['date_start'][0:4]
		
		if last_year != year:
			if last_year is not None: print()
			last_year = year
		
		print('{0: <6}'.format(str(i)), end = ' ')
		print(course['date_start'], end = '  ')
		print(course['code'], end = '   ')
		print(course['name_current'])
		
		i += 1
	
	print('\nange index för den kurs du vill hantera smeknamn för:')
	course_choice = input('>> ')
	
	print()
	
	if len(course_choice) == 0:
		print('avslutar')
		break
	
	try:
		course_choice = int(course_choice) - 1
		course = courses[course_choice]
	
	except:
		print('ogiltigt val, försök igen')
		continue
	
	set_nickname(course)
