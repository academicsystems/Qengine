import base64
import mimetypes
mimetypes.init()
import json
import qhelper
import requests

def process_python2_code(key,pycode,reqvars,qenginevars,cachedresources,genfiles):
	# substitute any qengine vars into sage code
	subblock = qhelper.substitute_vars(pycode,qenginevars)
	
	# run code & get variables (key is py block namespace, check if there are reqvars for it)
	if key in reqvars:
		pyjson = {"python":subblock,"vars":reqvars[key]}
	else:
		pyjson = {"python":subblock,"vars":[]}
	
	header = {'Content-Type':'application/json','Accept':'application/json'}
	response = requests.post(PYTHON2_URL + '/python',data = json.dumps(pyjson),headers = header)
	try:
		qenginevars[key] = response.json()
	except:
		qenginevars['error'] = 'invalid response received from python2.7 container'
	
	# retrieve any files that vars point to
	for ns, vars in qenginevars.iteritems():
		if ns != 'error':
			for key, vals in vars.iteritems():
				if key[0] == '_':
					filename = vals[0]
					if filename.split('.')[0] == 'error' or filename in cachedresources:
						continue
					
					mt = mimetypes.guess_type(filename)[0]
					response = requests.get(PYTHON2_URL + '/static/' + filename) # request for file's binary content
					if response.status_code == 404:
						pass # report error somehow?
					elif len(response.content) == 0:
						pass # probably means .sobj was saved & author needs to save different object
					else:
						genfiles.append({
							"content" : base64.b64encode(response.content),
							"encoding" : "base64",
							"filename" : filename,
							"mimeType" : mt,
						})
