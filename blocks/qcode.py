import base64
import mimetypes
mimetypes.init()
import json
import requests

### this is a generic function for sending code to any code service.
#
# The code service should accept requests at /code with a json payload of {'code':code,'vars':reqvars}
#
#

def process_any_code(key,code,reqvars,qenginevars,cachedresources,genfiles,question_errors):
	# run code & get variables (key is py block namespace, check if there are reqvars for it)
	if key in reqvars:
		cjson = {"code":code,"vars":reqvars[key]}
	else:
		cjson = {"code":code,"vars":[]}
	
	header = {'Content-Type':'application/json','Accept':'application/json'}
	response = requests.post(CODE_URL + '/code',data = json.dumps(cjson),headers = header)
	try:
		qenginevars[key] = response.json()
	except:
		question_errors.append('invalid response received from code service, ' + key)
	
	# retrieve any files that vars point to
	for ns, vars in qenginevars.iteritems():
		if ns != 'error':
			for key, vals in vars.iteritems():
				if key[0] == '_':
					filename = vals[0]
					if filename.split('.')[0] == 'error' or filename in cachedresources:
						continue
					
					mt = mimetypes.guess_type(filename)[0]
					response = requests.get(CODE_URL + '/static/' + filename) # request for file's binary content
					if response.status_code == 404:
						question_errors.append('unable to retrieve code generated resource, ' + filename)
						pass
					elif len(response.content) == 0:
						question_errors.append('code generated resource is size 0, might indicate bad save code, ' + filename)
						pass
					else:
						genfiles.append({
							"content" : base64.b64encode(response.content),
							"encoding" : "base64",
							"filename" : filename,
							"mimeType" : mt,
						})
