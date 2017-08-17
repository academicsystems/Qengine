import base64
from Crypto.Cipher import AES # pycrypto
import glob
import json
import Levenshtein
import mimetypes
import munkres
import re
import requests

###
###
###
###
### function used locally

def assemble_question_input(shortcode):
	parts = shortcode.split(":")
	
	if len(parts) != 3:
		# report error?
		return ''
	
	# 1 -> name, 3 -> type, 5 -> extra
	input = ['<input name="','','" type="','','" ','',' >']
	
	input[1] = '%%IDPREFIX%%qform_data[' + parts[0] + ']'
	
	itype = parts[1].lower()
	if itype == 'checkbox':
		olabel = '<label style="display:block" for="%%IDPREFIX%%qform_data[' + parts[0] + ']">'
		input[3] = 'checkbox'
		input[5] = 'id="%%IDPREFIX%%qform_data[' + parts[0] + ']" value="' + parts[2].split(',')[0] + '"'
		finput = olabel + ''.join(input) + parts[2].split(',')[1] + '</label>'
	elif itype == 'text':
		input[3] = 'text'
		input[5] = 'placeholder="' + parts[2] + '"'
		finput = ''.join(input)
	elif itype == 'number':
		input[3] = 'number'
		input[5] = 'placeholder="' + parts[2] + '"'
		finput = ''.join(input)
	elif itype == 'select':
		oselect = '<select style="width:100%" name="%%IDPREFIX%%qform_data[' + parts[0] + ']">'
		alloptions = ''
		options = parts[2].split(',')
		for option in options:
			alloptions += '<option>' + option + '</option>'
		finput = oselect + alloptions + '</select>'
	elif itype == 'multiple':
		oselect = '<select style="width:100%" name="%%IDPREFIX%%qform_data[' + parts[0] + '][]" multiple>'
		alloptions = ''
		options = parts[2].split(',')
		for option in options:
			alloptions += '<option>' + option + '</option>'
		finput = oselect + alloptions + '</select>'
	elif itype == 'submit':
		input[3] = 'submit'
		input[5] = 'value="' + parts[2] + '"'
		finput = ''.join(input)
	elif itype == 'reset':
		input[3] = 'reset'
		input[5] = 'value="' + parts[2] + '"'
		finput = ''.join(input)
	else:
		# report error ?
		finput = ''
	
	return finput

def get_stubs(delimiter,text):
	stubs = []
	for line in iter(text.splitlines(True)):
		matches = re.findall(delimiter + '(.*)' + delimiter, line)
		if len(matches) > 0:
			for match in matches:
				stubs.append(match)
	
	return stubs

def setifset(obj,key):
	if key in obj:
		return {key:obj[key]}
	else:
		return None

###
###
###
###
### functions used in Qengine + Blocks

def get_first_file(filename):
	files = glob.glob(filename + "*")
	if len(files) > 0:
		return files[0]
	else:
		return None

def get_local_files(filetext,qpath,genfiles):
	lines = filetext.splitlines()
	for line in lines:
		path = line.strip()
		if 'http' in path:
			response = requests.get(path)
			if response.status_code == 404:
				filecontent = None # report error somehow?
			else:
				filecontent = response.content
				filename = path.split("/")[-1]
		else:
			# local files must be in question folder, no path changing allowed
			if '..' in path or '/' in path:
				filecontent = None
			else:
				with open(qpath + "/" + path,"r") as file:
					filecontent = file.read()
					filename = path
		
		if filecontent is not None:
			mt = mimetypes.guess_type(filename)[0]
			genfiles.append({
				"content" : base64.b64encode(filecontent),
				"encoding" : "base64",
				"filename" : filename,
				"mimeType" : mt,
			})

# filestr - string of block
# reqvars - dict of vars like: {'namespace':['varname']}
def get_reqvars(filestr,reqvars):
	currentvars = []
	for line in iter(filestr.splitlines(True)):
		matches = re.findall('@@(.*?)@@', line)
		if len(matches) > 0:
			for match in matches:
				# only add matches once
				if match not in currentvars:
					currentvars.append(match)
	
	for variable in currentvars:
		splitvar = variable.split('.')
		if(len(splitvar) != 2): 
			return None
		if splitvar[0] not in reqvars:
			reqvars[splitvar[0]] = []
		if splitvar[1] not in reqvars[splitvar[0]]:
			reqvars[splitvar[0]].append(splitvar[1])
	
	return reqvars

def store_vars_in_html(varblock,qenginevars,salt,iv):
	vhtml = ''
	lines = varblock.splitlines(True)
	for line in lines:
		aesObj = AES.new(salt, AES.MODE_CFB, iv) # has to be created for each encrypt
		name = line.strip()
		nparts = name.split('.')
		try:
			value = str(qenginevars[nparts[1]][nparts[2]][0])
		except:
			value = '' # invalid variable name or requested variable doesn't exist
		vhtml += "<input type='hidden' name='%%IDPREFIX%%qform_data[" + name + "]' value='" + base64.b64encode(aesObj.encrypt(value)) + "'>"
	
	return vhtml

def substitute_shortcodes(sblock):
	delimiter = '~~~'
	fblock = ''
	for line in iter(sblock.splitlines(True)):
		matches = re.findall(delimiter + '(.*?)' + delimiter, line)
		if len(matches) > 0:
			for match in matches:
				replacestub = assemble_question_input(match)
				replaceme = r"" + re.escape(delimiter + match + delimiter)
				line = re.sub(replaceme,replacestub,line)
		fblock += line
	
	return fblock

def substitute_vars(sblock,vars):
	fblock = ''
	lines = sblock.splitlines(True)
	for line in lines:
		matches = re.findall('@@(.*?)@@', line)
		if len(matches) > 0:
			for match in matches:
				keys = match.split('.')
				try:
					replacestub = vars[keys[0]][keys[1]][0] # this grabs text, but what if LaTeX is wanted, stored at index 1 !!!!!!!!!!!!!!!!!!
				except Exception as e:
					replacestub = ''
				replaceme = r"" + re.escape('@@' + match + '@@')
				line = re.sub(replaceme,str(replacestub),line)
		fblock += line
	
	return fblock

