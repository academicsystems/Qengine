import base64
import json
import threading

class SaveToCache(threading.Thread):
	def __init__(self, qenginevars, genfiles, sessionDataPath, sessionDataDir):
		threading.Thread.__init__(self)
		self.qenginevars = qenginevars
		self.genfiles = genfiles
		self.sessionDataPath = sessionDataPath
		self.sessionDataDir = sessionDataDir
	
	def run(self):
		with open(self.sessionDataPath, 'w') as sessionjsonfile:
			json.dump(self.qenginevars, sessionjsonfile)
		
		for file in self.genfiles:
			with open(self.sessionDataDir + '/'+ file['filename'],'wb') as sessionfile:
				sessionfile.write(base64.b64decode(file['content']))