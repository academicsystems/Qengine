#!/usr/bin/python2.7

#
#
### These are tests that can be performed with only core Qengine blocks
#
#

import json
import unittest

class QengineTestCase(unittest.TestCase):
	
	@classmethod
	def setUpClass(self):
		from pkg.config.qconfig import Config
		self.config = Config()
		self.config.init({
			'QENGINE_SALT':'must_be_16_24_or_32_chars_long__',
			'QENGINE_QUESTION_LOCATION':'',
			'QENGINE_CACHE_DIR':'',
			'QENGINE_ENABLE_REMOTE':True,
			'QENGINE_IV':'must_be_16_long_',
			'QENGINE_LOG_REQUESTS':False,
			'QENGINE_MOOLE_HACKS':True,
			'QENGINE_NO_CACHE':True,
			'QENGINE_PASSKEY':None,
			'ENGINEINFO_name':'Engine Testing',
			'PYTHON2_URL':'http://qpython2:9602',
			'SAGE_URL':'http://qsage:9601'
		})
		
		from pkg.routes import app
		self.app = app.test_client()
		self.app.testing = True
	
	@classmethod
	def tearDownClass(self):
		pass
	
	def setUp(self):
		pass

	def tearDown(self):
		self.config.QENGINE_PASSKEY = None
	
	def test_root(self):
		result = self.app.get('/') 
		self.assertEqual(result.status_code,404)
	
	def test_getEngineInfo_NoPasskey(self):
		result = self.app.get('/info')
		self.assertEqual(result.status_code,200)
		
		data = json.loads(result.data)
		self.assertIn('engineinfo',data)
		
		self.assertNotIn('errors',data)
	
	def test_getEngineInfo_NoPasskey(self):
		self.config.QENGINE_PASSKEY = 'must_be_16_24_or_32_chars_long__'
		result = self.app.get('/info')
		
		data = json.loads(result.data)
		self.assertIn('error',data)
	
	def test_getEngineInfo_ValidPasskey(self):
		self.config.QENGINE_PASSKEY = 'must_be_16_24_or_32_chars_long__'
		result = self.app.get('/info?passKey=sNiHvH1axA%3D%3D:SKLEFEPVTRQNJDYI')
		
		data = json.loads(result.data)
		self.assertIn('engineinfo',data)
		
		self.assertNotIn('errors',data)
	
	def test_getEngineInfo_InvalidPasskey(self):
		self.config.QENGINE_PASSKEY = 'must_be_16_24_or_32_chars_long__'
		result = self.app.get('/info?passKey=qwertyuiop%3D%3D:QWERTYUIOPASDFGH')
		
		data = json.loads(result.data)
		self.assertIn('error',data)
	
	def test_getQuestionMetadata_MissingQuestion(self):
		result = self.app.get('/question/does/not/exist')
		self.assertEqual(result.status_code,404)
		
		data = json.loads(result.data)
		self.assertIn('error',data)
	
	def test_stop_BadRoute(self):
		result = self.app.delete('/session/../1234')
		self.assertEqual(result.status_code,400)
	
	def test_stop(self):
		result = self.app.delete('/session/1234')
		
		self.assertEqual(result.status_code,200)
	

if __name__ == '__main__':
	unittest.main()
