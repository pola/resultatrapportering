#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests, re, html, json, getpass

print('ange ditt KTH-användarnamn (utan @kth.se):')
username = input('> ')
print()

print('ange ditt lösenord:')
password = getpass.getpass('> ')
print()

s = requests.session()

r = s.get(url = 'https://kth.instructure.com/login')

action = re.search('<form name="form1" action="(.*?)" method="post">', r.text).group(1)

post_data = {
	'shib_idp_ls_exception.shib_idp_session_ss': '', 
	'shib_idp_ls_success.shib_idp_session_ss': 'true',
	'shib_idp_ls_value.shib_idp_session_ss': '',
	'shib_idp_ls_exception.shib_idp_persistent_ss': '',
	'shib_idp_ls_success.shib_idp_persistent_ss': 'true',
	'shib_idp_ls_value.shib_idp_persistent_ss': '',
	'shib_idp_ls_supported': 'true',
	'_eventId_proceed': ''
}

r = s.post(url = 'https://saml-5.sys.kth.se' + action, data = post_data)

action = re.search('<form id="fm1" action="(.*?)" method="post">', r.text).group(1)
lt = re.search('<input type="hidden" name="lt" value="(.*?)" />', r.text).group(1)
execution = re.search('<input type="hidden" name="execution" value="(.*?)" />', r.text).group(1)

post_data = {
	'username': username,
	'password': password,
	'lt': lt,
	'execution': execution,
	'_eventId': 'submit',
	'subimt': 'Logga in'
}

r = s.post(url = 'https://login.kth.se' + action, data = post_data)

action = html.unescape(re.search('<form action="(.*?)" method="post">', r.text).group(1))
saml_response = html.unescape(re.search('<input type="hidden" name="SAMLResponse" value="(.*?)"/>', r.text).group(1))

post_data = {
	'SAMLResponse': saml_response
}

r = s.post(url = action, data = post_data)

r = s.get(url = 'https://kth.instructure.com/profile/settings')

authenticity_token = re.search('<input type="hidden" name="authenticity_token" value="(.*?)" />', r.text).group(1)

post_data = {
	'utf8': '',
	'authenticity_token': authenticity_token,
	'purpose': 'resultatrapportering',
	'access_token[purpose]': 'resultatrapportering',
	'expires_at': '',
	'access_token[expires_at]': '',
	'_method': 'post'
}

r = s.post(url = 'https://kth.instructure.com/profile/tokens', data = post_data)
access_token = json.loads(r.text)
access_token = access_token['visible_token']

fh = open('hemlig-nyckel.txt', 'w')
fh.write(access_token)
fh.close()

print('nyckel sparad i hemlig-nyckel.txt')
