import base64
import mimetypes
mimetypes.init()
import json
import qhelper
import requests

def process_sage_code(key,sagecode,reqvars,qenginevars,cachedresources,genfiles):
	# substitute any qengine vars into sage code
	subblock = qhelper.substitute_vars(sagecode,qenginevars)
	
	# run code & get variables (key is sage block namespace, check if there are reqvars for it)
	if key in reqvars:
		sagejson = {"sage":subblock,"vars":reqvars[key]}
	else:
		sagejson = {"sage":subblock,"vars":[]}
	
	header = {'Content-Type':'application/json','Accept':'application/json'}
	response = requests.post(SAGE_URL + '/sage',data = json.dumps(sagejson),headers = header)
	try:
		qenginevars[key] = response.json()
	except:
		qenginevars['error'] = 'invalid response received from sagemath'
	
	# retrieve any files that vars point to
	for ns, vars in qenginevars.iteritems():
		for key, vals in vars.iteritems():
			if key[0] == '_':
				filename = vals[0]
				if filename.split('.')[0] == 'error' or filename in cachedresources:
					continue
				
				mt = mimetypes.guess_type(filename)[0]
				response = requests.get(SAGE_URL + '/static/' + filename) # request for file's binary content
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
