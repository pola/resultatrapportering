#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import requests
from canvas import get_courses, get_list, get_object, Student

content_types = {
	'application/pdf': 'pdf',
	'text/plain': 'txt'
}

if len(sys.argv) != 3:
	print('kör så här: inlämningshämtare.py <(del av) kurs-namn> <uppgiftsnamn>')
	sys.exit(1)

courses = get_courses(sys.argv[1])


if len(courses) == 0:
	print('hittade ej angiven kurs')
	sys.exit(1)

elif len(courses) == 1:
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

assignments = course.get_assignments()
assignment = next((a for a in assignments if a.name == sys.argv[2]), None)

if assignment is None:
	print('hittade ej angiven uppgift')
	sys.exit(1)

try:
	fh = open('e-postadresser.txt', 'r')
	email_addresses = [x.strip().lower() for x in fh.readlines()]
	email_addresses = [x for x in email_addresses if len(x) > 0]
	fh.close()
	
	if len(email_addresses) == 0:
		print('filen e-postadresser.txt verkar vara tom')
		sys.exit(1)
	
	print('sparar endast inlämningar för de i e-postadresser.txt...')

except:
	email_addresses = []
	print('sparar alla inlämningar för ' + str(course) + '...')

submissions = get_list('/courses/' + str(course.id) + '/assignments/' + str(assignment.id) + '/submissions?include[]=user')
submissions = [s for s in submissions if 'attachments' in s and len(s['attachments']) > 0]

saved_email_addresses = set()

for submission in submissions:
	student = Student(submission['user'])
	
	if len(email_addresses) > 0 and student.email_address not in email_addresses:
		continue
	
	print(student)
	
	i = 1
	
	for attachment in submission['attachments']:
		if attachment['content-type'] not in content_types:
			print('\thoppar över ' + attachment['display_name'])
			continue
		
		response = requests.get(attachment['url'])
		
		user_name = student.email_address.split('@kth.se')[0]
		file_name = user_name + '-' + str(i) + '.' + content_types[attachment['content-type']]
		
		fh = open(file_name, 'wb')
		fh.write(response.content)
		fh.close()
		
		saved_email_addresses.add(student.email_address)
		
		i += 1

if len(email_addresses) > 0:
	unhandled_email_addresses = [x for x in email_addresses if x not in saved_email_addresses]
	
	if len(unhandled_email_addresses) == 0:
		print('samtliga giltiga inlämningar från studenter i e-postadresser.txt sparades')
	
	else:
		print('dessa studenter i e-postadresser.txt saknade giltiga inlämningar:')
		for email_address in unhandled_email_addresses: print('\t' + email_address)
