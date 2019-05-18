# -*- coding: utf-8 -*-

# Den här filen innehåller hjälpfunktioner som används av skripten.

import requests, sys, re, dateutil.parser

g_base = 'https://kth.instructure.com/api/v1'
g_grading_schemes = {}
g_access_token = -1


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
		
		response_this = requests.get(url = url, headers = { 'Authorization': 'Bearer ' + get_access_token() })
		response_list = response_this.json()
		
		if type(response_list) is not list: return response_list
		
		response += response_list
	
		url = None
	
		if 'Link' in response_this.headers:
			r = re.search('<([^>]+?)>; rel="next"', response_this.headers['Link'])
		
			if r is not None: url = r.group(1)
		
	return response


def get_object(url):
	return requests.get(url = g_base + url, headers = { 'Authorization': 'Bearer ' + get_access_token() }).json()


def put(url, data):
	return requests.put(url = g_base + url, headers = { 'Authorization': 'Bearer ' + get_access_token() }, data = data).json()


def post(url, data):
	return requests.post(url = g_base + url, headers = { 'Authorization': 'Bearer ' + get_access_token() }, data = data).json()


def delete(url):
	return requests.delete(url = g_base + url, headers = { 'Authorization': 'Bearer ' + get_access_token() }).json()


def get_access_token():
	global g_access_token
	
	if g_access_token == -1:
		try:
			fh = open('hemlig-nyckel.txt', 'r')
			g_access_token = fh.read().strip()
			fh.close()
			
		except:
			g_access_token = None
	
	return g_access_token


def nice_grade(grade):
	if grade is None: return '-'
	
	grade = str(grade)
	
	if grade == '' : return '-'
	if grade == 'incomplete': return 'F'
	if grade == 'complete': return 'P'
	
	return grade
