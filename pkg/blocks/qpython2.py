import base64
import mimetypes
mimetypes.init()
import json
import requests

# key - block namespace
# sagecode - block contents
#
# reqvars - required variables dict
# qenginevars - retrieved variables dict
# cachedresources - list of cached resources dict
# genfiles - list of generated resources dict
#
def process_python2_code(key,pycode,reqvars,qenginevars,cachedresources,genfiles,question_errors):
	# run code & get variables (key is py block namespace, check if there are reqvars for it)
	if key in reqvars:
		pyjson = {"python":pycode,"vars":reqvars[key]}
	else:
		pyjson = {"python":pycode,"vars":[]}
	
	header = {'Content-Type':'application/json','Accept':'application/json'}
	response = requests.post(PYTHON2_URL + '/python',data = json.dumps(pyjson),headers = header)
	try:
		qenginevars[key] = vars = response.json()
	except:
		question_errors.append('invalid response received from python2.7 service, ' + key)
		return
	
	# retrieve any files that vars point to
	for key, vals in vars.iteritems():
		if key == 'error':
			question_errors.append('python2 block error: ' + vals[0])
			continue
		
		if key[0] == '_':
			filename = vals[0]
			if filename.split('.')[0] == 'error' or filename in cachedresources:
				continue
			
			mt = mimetypes.guess_type(filename)[0]
			response = requests.get(PYTHON2_URL + '/static/' + filename) # request for file's binary content
			if response.status_code == 404:
				question_errors.append('unable to retrieve sagemath generated resource, ' + filename)
				pass
			elif len(response.content) == 0:
				question_errors.append('python2.7 generated resource is size 0, might indicate bad save code, ' + filename)
				pass
			else:
				genfiles.append({
					"content" : base64.b64encode(response.content),
					"encoding" : "base64",
					"filename" : filename,
					"mimeType" : mt,
				})
