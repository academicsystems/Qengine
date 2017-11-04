#!/usr/bin/python2.7

import json
import unittest

#
#
### These are tests that require the example_questions & the Sage and Python2.7 block services
#
#


class QengineTestCase(unittest.TestCase):
	
	@classmethod
	def setUpClass(self):
		from pkg.config.qconfig import Config
		self.config = Config()
		self.config.init({
			'QENGINE_SALT':'must_be_16_24_or_32_chars_long__',
			'QENGINE_QUESTION_LOCATION':'filesystem',
			'QENGINE_CACHE_DIR':'',
			'QENGINE_ENABLE_REMOTE':True,
			'QENGINE_IV':'must_be_16_long_',
			'QENGINE_LOG_REQUESTS':False,
			'QENGINE_MOODLE_HACKS':True,
			'QENGINE_NO_CACHE':True,
			'QENGINE_PASSKEY':'',
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
	
	def test_getQuestionMetadata(self):
		result = self.app.get('/question/graph_theory/spanning_trees/1.0')
		self.assertEqual(result.status_code,200)
		
		data = json.loads(result.data)
		self.assertIn('questionmetadata',data)
	
	def test_start(self):
		postdata = '{"questionID":"spanning_trees","questionVersion":"1.0","questionBaseURL":"graph_theory","initialParamNames":["randomseed"],"initialParamValues":[807031909],"cachedResources":["sage_logo_new_l_hc_edgy-nq8.png"]}'
		
		result = self.app.post('/session',data=postdata,follow_redirects=True)
		self.assertEqual(result.status_code,200)
		self.assertEqual(result.mimetype,'application/json')
		
		data = json.loads(result.data)
		self.assertIn('CSS',data)
		self.assertIn('XHTML',data)
		self.assertIn('progressInfo',data)
		self.assertIn('questionSession',data)
		self.assertIn('resources',data)
		
		# generated file
		self.assertIn('content',data['resources'][0])
		self.assertIn('mimeType',data['resources'][0])
		self.assertIn('filename',data['resources'][0])
		self.assertIn('encoding',data['resources'][0])
		
		# remote file
		self.assertIn('content',data['resources'][1])
		self.assertIn('mimeType',data['resources'][1])
		self.assertIn('filename',data['resources'][1])
		self.assertIn('encoding',data['resources'][1])
		
		# local file
		self.assertIn('content',data['resources'][1])
		self.assertIn('mimeType',data['resources'][1])
		self.assertIn('filename',data['resources'][1])
		self.assertIn('encoding',data['resources'][1])
		
		self.assertNotIn('errors',data)
	
	def test_start_noJson(self):
		result = self.app.post('/session',data='',follow_redirects=True)
		self.assertEqual(result.status_code,200)
		
		data = json.loads(result.data)
		self.assertIn('error',data)
	
	def test_start_PassKeyRequired(self):
		self.config.QENGINE_PASSKEY = 'must_be_16_24_or_32_chars_long__'
		
		postdata = '{"questionID":"spanning_trees","questionVersion":"1.0","questionBaseURL":"graph_theory","initialParamNames":["randomseed","passKey"],"initialParamValues":[807031909,"sNiHvH1axA%3D%3D:SKLEFEPVTRQNJDYI"],"cachedResources":["sage_logo_new_l_hc_edgy-nq8.png"]}'
		
		result = self.app.post('/session',data=postdata,follow_redirects=True)
		self.assertEqual(result.status_code,200)
		
		data = json.loads(result.data)
		self.assertNotIn('errors',data)
	
	def test_process(self):
		postdata = '{"values": ["16","0","Submit","qJGHmQZh8Hf6jg==","qJM=","qQ==","%2Fc0DhBbrDQ%3D%3D:SvDk1yiTxNO8WLci"],"names":["myq_answer","myq_guess","mynm_submit","temp_qengine_randomseed","perm_mysage_answer","temp_qengine_step","qengine.passKey"]}'
		
		result = self.app.post('/session/graph_theory/spanning_trees/1.0/807031909',data=postdata,follow_redirects=True)
		self.assertEqual(result.status_code,200)
		
		data = json.loads(result.data)
		self.assertIn('CSS',data)
		self.assertIn('XHTML',data)
		self.assertIn('progressInfo',data)
		self.assertIn('questionEnd',data)
		self.assertIn('resources',data)
		
		self.assertIn('results',data)
		self.assertIn('answerLine',data['results'])
		self.assertIn('customResults',data['results'])
		self.assertIn('actionSummary',data['results'])
		self.assertIn('attempts',data['results'])
		self.assertIn('questionLine',data['results'])
		self.assertIn('scores',data['results'])
		
		self.assertIn('marks',data['results']['scores'][0])
		self.assertIn('axis',data['results']['scores'][0])
		
		data = json.loads(result.data)
		self.assertNotIn('errors',data)
	
	def test_process_noJson(self):
		result = self.app.post('/session/graph_theory/s	panning_trees/1.0/807031909',data='',follow_redirects=True)
		self.assertEqual(result.status_code,200)
		
		data = json.loads(result.data)
		self.assertIn('error',data)
	
	def test_process_PassKeyRequired(self):
		self.config.QENGINE_PASSKEY = 'must_be_16_24_or_32_chars_long__'
		
		postdata = '{"values": ["16","0","Submit","qJGHmQZh8Hf6jg==","qJM=","qQ==","%2Fc0DhBbrDQ%3D%3D:SvDk1yiTxNO8WLci"],"names":["myq_answer","myq_guess","mynm_submit","temp_qengine_randomseed","perm_mysage_answer","temp_qengine_step","qengine.passKey"]}'
		
		result = self.app.post('/session/graph_theory/spanning_trees/1.0/807031909',data=postdata,follow_redirects=True)
		self.assertEqual(result.status_code,200)
		
		data = json.loads(result.data)
		self.assertNotIn('errors',data)

if __name__ == '__main__':
	unittest.main()
