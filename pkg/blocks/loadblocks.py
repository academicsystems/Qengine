import requests

def checkBlockContainer(configuration,name):
	if name not in configuration:
		return False

	url = configuration[name]
	if type(url) is not str:
		print 'WARNING: No url in config info for ' + name
		return False
	
	bounced = False
	try:
		response = requests.get(url + '/')
		if response.status_code != 200:
			bounced = True
	except:
		bounced = True
	
	if bounced:	
		print 'WARNING: Could not contact ' + name + ' at ' + url
		return False
	return True

def loadblocks(configuration):
	BLOCKS = {}
	
	# just an empty line to make test output prettier
	print ''
	
	if checkBlockContainer(configuration,'PYTHON2_URL'):
		import qpython2
		qpython2.PYTHON2_URL = configuration['PYTHON2_URL']
		BLOCKS['python2'] = qpython2.process_python2_code
		print 'SUCCESS: PYTHON2 enabled'
	
	if checkBlockContainer(configuration,'SAGE_URL'):
		import qsage
		qsage.SAGE_URL = configuration['SAGE_URL']
		BLOCKS['sage'] = qsage.process_sage_code
		print 'SUCCESS: SAGE enabled'
	
	#! TODO: check for generic code blocks, like CODE_URL_name. import qcode as object when found 
	
	return BLOCKS