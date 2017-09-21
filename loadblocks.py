import requests

def checkBlockContainer(configuration,name):
	if name not in configuration:
		print 'No url in config info for ' + name
		return False

	url = configuration[name]
	if type(url) is not str:
		print 'No url in config info for ' + name
		return False
	
	bounced = False
	try:
		response = requests.get(url + '/')
		if response.status_code != 200:
			bounced = True
	except:
		bounced = True
	
	if bounced:	
		print 'Could not contact ' + name + ' at ' + url
		return False
	return True

def loadblocks(configuration):
	BLOCKS = {}
	
	if checkBlockContainer(configuration,'PYTHON2_URL'):
		import qpython2
		qpython2.PYTHON2_URL = configuration['PYTHON2_URL']
		BLOCKS['python2'] = qpython2.process_python2_code
		print 'PYTHON2 enabled'
	
	if checkBlockContainer(configuration,'SAGE_URL'):
		import qsage
		qsage.SAGE_URL = configuration['SAGE_URL']
		BLOCKS['sage'] = qsage.process_sage_code
		print 'SAGE enabled'
	
	#! TODO: check for generic code blocks, like CODE_URL_name. import qcode as object when found 
	
	return BLOCKS