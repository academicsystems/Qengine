import os.path
from random import choice
from string import ascii_uppercase
import sys
import yaml # pyyaml

from ..blocks import loadblocks as lb

def _loadConfigOption(key,default,configuration):
	try:
		value = configuration[key]
		if type(value) is str:
			if len(value) == 0:
				value = default
	except:
		value = default
	
	return value

if os.path.isfile('./configuration.yaml'):
	config_file = './configuration.yaml';
elif os.path.isfile('./default-configuration.yaml'):
	config_file = './default-configuration.yaml';
	print 'WARNING: Using default-configuration.yaml. You should supply your own configuration.yaml file'
else:
	print 'FATAL ERROR: Could not find configuration.yaml file!'
	sys.exit()

with open(config_file,'r') as f:
	configuration = yaml.load(f.read())
	
	try:
		QENGINE_CACHE_DIR = configuration['QENGINE_CACHE_DIR']
		QENGINE_SALT = configuration['QENGINE_SALT']
	except Exception as e:
		print e
		sys.exit()
		
	validSaltLengths = [16,24,32]
	if len(QENGINE_SALT) not in validSaltLengths:
		print 'QENGINE_SALT must be 16, 24, or 32 bytes long'
		sys.exit()
	
	try:
		QENGINE_IV = configuration['QENGINE_IV']
		if len(QENGINE_SALT) not in validSaltLengths:
			print 'QENGINE_IV must be 16 bytes long'
			sys.exit()
	except:
		QENGINE_IV = ''.join(choice(ascii_uppercase) for i in range(16))
	
	# optional environment variables
	QENGINE_LOG_REQUESTS = _loadConfigOption('QENGINE_LOG_REQUESTS',False,configuration)
	QENGINE_MOODLE_HACKS = _loadConfigOption('QENGINE_MOODLE_HACKS',False,configuration)
	QENGINE_NO_CACHE = _loadConfigOption('QENGINE_NO_CACHE',False,configuration)
	QENGINE_PASSKEY = _loadConfigOption('QENGINE_PASSKEY',None,configuration)
	
	ENGINEINFO = {}
	
	# engine info
	for key in configuration:
		if 'ENGINEINFO_' in key:
			ekey = key.split('_',1)[1]
			if len(ekey) > 0:
				ENGINEINFO[ekey] = configuration[key]
	
	BLOCKS = lb.loadblocks(configuration)