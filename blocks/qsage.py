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
def process_sage_code(key,sagecode,reqvars,qenginevars,cachedresources,genfiles,question_errors):	
	# run code & get variables (key is sage block namespace, check if there are reqvars for it)
	if key in reqvars:
		sagejson = {"sage":sagecode,"vars":reqvars[key]}
	else:
		sagejson = {"sage":sagecode,"vars":[]}
	
	header = {'Content-Type':'application/json','Accept':'application/json'}
	response = requests.post(SAGE_URL + '/sage',data = json.dumps(sagejson),headers = header)
	try:
		qenginevars[key] = response.json()
	except:
		question_errors.append('invalid response received from sagemath service, ' + key)
	
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
					question_errors.append('unable to retrieve sagemath generated resource, ' + filename)
					pass
				elif len(response.content) == 0:
					question_errors.append('sagemath generated resource is size 0, might indicate bad save code, ' + filename)
					pass
				else:
					genfiles.append({
						"content" : base64.b64encode(response.content),
						"encoding" : "base64",
						"filename" : filename,
						"mimeType" : mt,
					})
