import os.path
from random import choice
from string import ascii_uppercase
import sys
import yaml # pyyaml

from ..blocks import loadblocks as lb

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Config(object):
	__metaclass__ = Singleton
	
	initialized = False
	
	# static config variables
	QENGINE_CACHE_DIR = ''
	QENGINE_SALT = ''
	QENGINE_IV = ''
	QENGINE_LOG_REQUESTS = False
	QENGINE_MOODLE_HACKS = False
	QENGINE_NO_CACHE = False
	QENGINE_PASSKEY = None
	
	ENGINEINFO = {}
	BLOCKS = {}
	
	def __init__(self):
		pass
	
	def _loadConfigOption(self,key,default,configuration):
		try:
			value = configuration[key]
			if type(value) is str:
				if len(value) == 0:
					value = default
		except:
			value = default
		
		return value
	
	def init(self,inconfig=None):
		if inconfig != None:
			configuration = inconfig
		else:
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
			
		#! set location of questions
		#
		# 1 - local files
		# 2 - mongodb
		# 3 - mysql
		# 4 - receive questions
		
		# mandatory environment variables
		try:
			self.QENGINE_SALT = configuration['QENGINE_SALT']
		except Exception as e:
			print e
			sys.exit()
			
		validSaltLengths = [16,24,32]
		if len(self.QENGINE_SALT) not in validSaltLengths:
			print 'QENGINE_SALT must be 16, 24, or 32 bytes long'
			sys.exit()
		
		try:
			self.QENGINE_IV = configuration['QENGINE_IV']
			if len(self.QENGINE_SALT) not in validSaltLengths:
				print 'QENGINE_IV must be 16 bytes long'
				sys.exit()
		except:
			self.QENGINE_IV = ''.join(choice(ascii_uppercase) for i in range(16))
		
		# optional environment variables
		self.QENGINE_LOG_REQUESTS = self._loadConfigOption('QENGINE_LOG_REQUESTS',False,configuration)
		self.QENGINE_MOODLE_HACKS = self._loadConfigOption('QENGINE_MOODLE_HACKS',False,configuration)
		self.QENGINE_NO_CACHE = self._loadConfigOption('QENGINE_NO_CACHE',False,configuration)
		self.QENGINE_PASSKEY = self._loadConfigOption('QENGINE_PASSKEY',None,configuration)
		
		# only required if no cache is false
		if not self.QENGINE_NO_CACHE:
			try:
				self.QENGINE_CACHE_DIR = configuration['QENGINE_CACHE_DIR']
			except Exception as e:
				print e
				sys.exit()
		
		self.ENGINEINFO = {}
		
		# engine info
		for key in configuration:
			if 'ENGINEINFO_' in key:
				ekey = key.split('_',1)[1]
				if len(ekey) > 0:
					self.ENGINEINFO[ekey] = configuration[key]
		
		self.BLOCKS = lb.loadblocks(configuration)
		
		self.initialized = True

