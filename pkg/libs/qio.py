import os
import os.path
import shutil
import time
import yaml # pyyaml

from ..config.qconfig import Config
from ..libs import qlog
from ..libs.qhelper import Qhelper

class Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]

#
# this class is for reading and writing question files depending on where they're stored
#
class Qio():
	__metaclass__ = Singleton
	
	# config - dict of qengine config keys and values
	def __init__(self):
		self.config = Config()
		self.qhelper = Qhelper()
	
	### PRIVATE FUNCTIONS
	
	def _getMetadataFileSystem(self,base,id):
		metadatafile = "./questions/" + base + "/" + id + "/" + "metadata"
		file = self.qhelper.get_first_file(metadatafile)
		if file is not None:
			try:
				with open(file,'r') as f:
					metadata = yaml.load(f.read())
				if metadata == None:
					return {'metadata':'empty'}
				else:
					return metadata
			except Exception as e:
				qlog.loge(str(e))
				return False
		else:
			return False
	
	def _getMetadataMySQL(self,base,id):
		return False
	
	def _getMetadataMongoDB(self,base,id):
		return False
	
	def _setMetadataFileSystem(self,base,id,metadata):
		metafilepath = "./questions/" + base + "/" + id + "/metadata";
		try:
			with open(metafilepath,'wb') as file:
				file.write("%s" % metadata)
		except Exception as e:
			qlog.loge(str(e))
			return False
		
		return True
	
	def _setMetadataMySQL(self,base,id,metdata):
		return False
	
	def _setMetadataMongoDB(self,base,id,metdata):
		return False
	
	def _getQuestionFileSystem(self,base,id,version):
		qdirname = "./questions/" + base + "/" + id + "/" + version
		qfile = self.qhelper.get_first_file(qdirname + "/question")
		
		try:
			with open(qfile) as f:
				lines = f.read()
		except Exception as e:
			qlog.loge(str(e))
			return False
		
		return lines
	
	def _getQuestionMySQL(self,base,id,version):
		return False
	
	def _getQuestionMongoDB(self,base,id,version):
		return False
		
	def _setQuestionFileSystem(self,base,id,version,questionFile,backup):
		qdirname = "./questions/" + base + "/" + id + "/" + version
		qfilepath = qdirname + "/" + "question"
		
		# create question if necessary, create backup if asked for
		if not os.path.isdir(qdirname):
			os.makedirs(qdirname,0750)
		elif os.path.isfile(qfilepath) and backup:
			stamp = str(time.time())
			shutil.move(qfilepath,qdirname + "/" + stamp + "_backup")
		
		try:
			with open(qfilepath,'wb') as file:
				file.write("%s" % questionFile)
		except Exception as e:
			qlog.loge(str(e))
			return False
		
		return True
	
	def _setQuestionMySQL(self,base,id,version,questionFile,backup):
		return False
	
	def _setQuestionMongoDB(self,base,id,version,questionFile,backup):
		return False	
	
	### PUBLIC FUNCTIONS
	
	# returns array or False
	def getMetadata(self,base,id):
		if self.config.QENGINE_QUESTION_LOCATION == 'filesystem':
			return self._getMetadataFileSystem(base,id)
		elif self.config.QENGINE_QUESTION_LOCATION == 'mysql':
			return self._getMetadataMySQL(base,id)
		elif self.config.QENGINE_QUESTION_LOCATION == 'mongodb':
			return self._getMetadataMongoDB(base,id)
		else:
			return False
	
	# returns True or False
	def setMetadata(self,base,id,metadata):
		if self.config.QENGINE_QUESTION_LOCATION == 'filesystem':
			return self._setMetadataFileSystem(base,id,metadata)
		elif self.config.QENGINE_QUESTION_LOCATION == 'mysql':
			return self._setMetadataMySQL(base,id,metadata)
		elif self.config.QENGINE_QUESTION_LOCATION == 'mongodb':
			return self._setMetadataMongoDB(base,id,metadata)
		else:
			return False
	
	# returns string or False
	def getQuestion(self,base,id,version):
		if self.config.QENGINE_QUESTION_LOCATION == 'filesystem':
			return self._getQuestionFileSystem(base,id,version)
		elif self.config.QENGINE_QUESTION_LOCATION == 'mysql':
			return self._getQuestionMySQL(base,id,version)
		elif self.config.QENGINE_QUESTION_LOCATION == 'mongodb':
			return self._getQuestionMongoDB(base,id,version)
		else:
			return False
	
	# returns True or False
	def setQuestion(self,base,id,version,questionFile,backup=False):
		if self.config.QENGINE_QUESTION_LOCATION == 'filesystem':
			return self._setQuestionFileSystem(base,id,version,questionFile,backup)
		elif self.config.QENGINE_QUESTION_LOCATION == 'mysql':
			return self._setQuestionMySQL(base,id,version,questionFile,backup)
		elif self.config.QENGINE_QUESTION_LOCATION == 'mongodb':
			return self._setQuestionMongoDB(base,id,version,questionFile,backup)
		else:
			return False
	
	
	