#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from canvas import get_courses, get_list, put, delete


def set_nickname(course):
	if course.name_original is None:
		print('Namn:              ' + course.name)
	
	else:
		print('Smeknamn:          ' + course.name)
		print('Ursprungligt namn: ' + course.name_original)
	
	print('Kurskod:           ' + course.code)
	print('Startdatum:        ' + course.date_start)
	
	print()
	
	if course.name_original is None: print('ange smeknamn:')
	else: print('ange nytt smeknamn, eller - för att rensa:')
	
	nickname = input('>> ')
	
	if len(nickname) == 0: print('avbryter')
	elif nickname == '-': delete('/users/self/course_nicknames/' + str(course.id))
	else: put('/users/self/course_nicknames/' + str(course.id), { 'nickname': nickname })
	
	print()



while True:
	courses = get_courses()
	courses.sort(key = lambda x: x.date_start + x.name)
	
	if len(courses) == 0:
		print('misslyckades med att hämta kurser -- felaktig nyckel?')
		sys.exit(1)
	
	print('index  startdatum  kurskod  namn')
	
	i = 1
	last_year = None
	
	for course in courses:
		year = course.date_start[0:4]
		
		if last_year != year:
			if last_year is not None: print()
			last_year = year
		
		print('{0: <6}'.format(str(i)), end = ' ')
		print(course.date_start, end = '  ')
		print(course.code, end = '   ')
		print(course.name)
		
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
