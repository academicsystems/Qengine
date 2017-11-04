import base64
from Crypto.Cipher import AES # pycrypto
import flask
from flask import Blueprint,jsonify,request
import json
import mimetypes
mimetypes.init()
import re

from ..config.qconfig import Config
from ..libs import parseblocks,qlog
from ..libs.qhelper import Qhelper
from ..libs.qio import Qio

qengine_process = Blueprint('qengine_process', __name__)
@qengine_process.route('/session/<path:sid>',methods=['POST'])
def process(sid):
	config = Config()
	qhelper = Qhelper()
	qio = Qio()
	
	# array of errors for question writers
	question_errors = []
	
	### INCOMING DATA ###
	
	data = flask.request.get_json()
	if data is None:
		try:
			data = json.loads(flask.request.data)
		except:
			nodata = {'error':'No json body detected or unable to parse request body'}
			return jsonify(nodata)
	
	# whatever inputs were in qhtml & whatever variables were in a {% qstore block, will be found here now
	formVars = dict(zip(data['names'],data['values']))
	
	# get variables from form data into qenginevars
	qenginevars = {}
	othervars = {}
	try:
		for key, value in formVars.iteritems():
			aesObj = AES.new(config.QENGINE_SALT, AES.MODE_CFB, config.QENGINE_IV)
			if config.QENGINE_MOODLE_HACKS:
				key = key.replace('_','.')
			splitkey = key.split('.')
			if len(splitkey) == 3:
				# base64 encoded & encrypted stored variable
				if splitkey[1] in qenginevars:
					qenginevars[splitkey[1]][splitkey[2]] = [aesObj.decrypt(base64.b64decode(value))] # has to be created for each decrypt
				else:
					qenginevars[splitkey[1]]= {}
					qenginevars[splitkey[1]][splitkey[2]] = [aesObj.decrypt(base64.b64decode(value))] # has to be created for each decrypt
				
				## !! splitkey[0] -> perm or temp, if perm : do something...
				
			elif len(splitkey) == 2:
				# some variable entered by student or manually created in qhtml
				if splitkey[0] in qenginevars:
					qenginevars[splitkey[0]][splitkey[1]] = [value]
				else:
					qenginevars[splitkey[0]] = {}
					qenginevars[splitkey[0]][splitkey[1]] = [value]
			else:
				# this is either something the LMS passed or an improperly formatted question variable
				othervars[key] = value
	except Exception as e:
		# this indicates a fatal error, as temp.qengine.step should always exist (at least one formVars value)
		qlog.loge(str(e))
	
	# check pass key if set	
	if config.QENGINE_PASSKEY != None:
		if 'passKey' not in qenginevars['qengine']:
			return jsonify({'error':'passkey is required'})
		presult = qhelper.checkPassKey(qenginevars['qengine']['passKey'][0])
		if presult == 1:
			return jsonify({'error':'passkey is required'})
		elif presult == 2:
			return jsonify({'error':'invalid passkey format'})
		elif presult == 3:
			return jsonify({'error':'invalid passkey'})
	
	### DETERMINE AND GET QUESTION STEP ###
	
	# parse next step in question
	step = int(qenginevars['qengine']['step'][0]) + 1
	
	# get path to question from sid: base/questionID/questionVersion/(language)/randomseed
	pathList = sid.split('/')
	
	try:
		base = pathList[0]
		id = pathList[1]
		version = pathList[2]
		if len(pathList) == 5:
			language = pathList[3]
			randomseed = pathList[4]
		else:
			language = ''
			randomseed = pathList[3]
	except:
		badfile = {'error':'Invalid path'}
		return flask.make_response(jsonify(badfile), 400)

	# used for file retrieval
	qpath = './questions/' + base + '/' + id + '/' + version

	qfile = qio.getQuestion(base,id,version)
	
	if qfile == False:
		return jsonify({'error':'question no longer exists'})
	
	# open and parse next step in question
	fileblocks = parseblocks.Blocks()
	step = fileblocks.checkStepConditional(qfile,step,qenginevars)
	fileblocks.parseString(qfile,step)
	
	if(len(fileblocks.errors) > 0):
		question_errors = question_errors + fileblocks.errors
	
	### GET REQUESTED VARIABLES ###
	
	reqvars = {}
	genfiles = []
	
	# get all requested variables here
	for key in fileblocks.blocks:
		# check block for conditional
		if fileblocks.blocks[key][2] is not None:
			reqvars = qhelper.add_to_reqvars(fileblocks.blocks[key][2],reqvars)
		
		# get reqvars for store block
		if fileblocks.blocks[key][0] == 'qstore':
			reqvars = qhelper.get_qstore_vars(fileblocks.blocks[key][1],reqvars)
			continue
		
		# grab vars from html & put in reqvars by namespace
		reqvars = qhelper.get_reqvars(fileblocks.blocks[key][1],reqvars)
		if reqvars is None:
			badfile = {'error':'invalid variable name in block, must be: blockname.name'}
			return flask.make_response(jsonify(badfile), 404)
	
	### CACHE cannot be used because there is the potential of:
	#		1. Two students miraculously get the same randomseed
	#		2. A variable or resource was generated based on the student's input
	#
	#	also, LMS only keeps its own cachedresources from start()
	
	### PROCESS BLOCKS ###
	
	# block: qcss
	qcss = ''
	# block: qhtml
	qhtml = ''
	# block: qstore
	vhtml = ''
	
	# grab content from different blocks
	result = None
	cachedresources = {}
	for key in fileblocks.order:
		# check if block has conditional variable to determine if it should be run
		procBlock = True
		if fileblocks.blocks[key][2] is not None:
			procBlock = qhelper.check_conditional(fileblocks.blocks[key][2],qenginevars)
		
		if procBlock:
			if fileblocks.blocks[key][0] == 'qcss':
				qcss += qhelper.substitute_vars(fileblocks.blocks[key][1],qenginevars)
			elif fileblocks.blocks[key][0] == 'files':
				qhelper.get_local_files(fileblocks.blocks[key][1],key,qpath,genfiles)
			elif fileblocks.blocks[key][0] == 'qans':
				try:
					resvar = qhelper.get_stubs('@@',fileblocks.blocks[key][1])[-1]
					resparts = resvar.split('.')
					result = float(qenginevars[resparts[0]][resparts[1]][0])
				except:
					result = 0
			elif fileblocks.blocks[key][0] == 'qhtml':
				qhtml += qhelper.substitute_vars(qhelper.substitute_shortcodes(fileblocks.blocks[key][1],qenginevars),qenginevars)
			elif fileblocks.blocks[key][0] == 'qstore':
				vhtml += qhelper.store_vars_in_html(fileblocks.blocks[key][1],qenginevars,config.QENGINE_SALT,config.QENGINE_IV)
			elif fileblocks.blocks[key][0] in config.BLOCKS:
				try:
					subblock = qhelper.substitute_vars(fileblocks.blocks[key][1],qenginevars)
					config.BLOCKS[fileblocks.blocks[key][0]](key,subblock,reqvars,qenginevars,cachedresources,genfiles,question_errors)
				except Exception as e:
					qlog.loge(str(e) + ' blocktype: ' + fileblocks.blocks[key][0])
	
	### FINAL RESPONSE ASSEMBLY
	
	questionEnd = False
	if result is not None:
		results = {
			"actionSummary" : '',
			"answerLine" : '',
			"attempts" : '',
			"customResults" : [],
			"questionLine" : '',
			"scores" : [
				{
					"axis" : "",
					"marks" : result
				}
			]
		}
		questionEnd = True
	else:
		results = ''
	
	### FOR TESTING PURPOSES, see what data is sent if we force a "-finish"
	#questionEnd = False
	#results = ''
	
	if "-finish" in othervars:
		questionEnd = True
		results = {
			"actionSummary" : "action summary",
			"answerLine" : "answer",
			"attempts" : step,
			"customResults" : [],
			"questionLine" : "question summary",
			"scores" : [
				{
					"axis" : "",
					"marks" : 0
				}
			]
		};
	
	aesObj = AES.new(config.QENGINE_SALT, AES.MODE_CFB, config.QENGINE_IV)
	stephtml = "<input type='hidden' name='%%IDPREFIX%%temp.qengine.step' value='" + base64.b64encode(aesObj.encrypt(str(step))) + "'>"
	
	# assemble final html with mathjax included	
	mjaxjs = """
	<script>
		var asciimath_divs = document.getElementsByClassName('qengine_asciimath');
		for(let i = 0; i < asciimath_divs.length; i++) {
			asciimath_divs[i].innerHTML = '`' + asciimath_divs[i].textContent + '`';
		}
		var latex_divs = document.getElementsByClassName('qengine_latex');
		for(let i = 0; i < latex_divs.length; i++) {
			latex_divs[i].innerHTML = '$$' + latex_divs[i].textContent + '$$';
		}
		
		window.onload = function () {
			function callback() {
				var asciimath_divs = document.getElementsByClassName('qengine_asciimath');
				for(let i = 0; i < asciimath_divs.length; i++) {
					MathJax.Hub.Queue(["Typeset",MathJax.Hub,asciimath_divs[i]]);
				}
				var latex_divs = document.getElementsByClassName('qengine_latex');
				for(let i = 0; i < latex_divs.length; i++) {
					MathJax.Hub.Queue(["Typeset",MathJax.Hub,latex_divs[i]]);
				}
			}
			
			var script = document.createElement('script');
			script.src = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js';
			script.type = 'text/javascript';
			script.innerHTML = "MathJax.Hub.Config({messageStyle:'none',jax:['input/TeX','output/HTML-CSS'],displayAlign:'left'});MathJax.Hub.Startup.onload();";
			script.async = true;
			done = false;
			script.onreadystatechange = script.onload = function() {
				if (!done && (!script.readyState || /loaded|complete/.test(script.readyState))) {
					done = true;
					callback();
				}
			};
			
			document.getElementsByTagName('head')[0].appendChild(script);
		}

	</script>
	"""
	
	xhtml = qhtml + vhtml + stephtml + mjaxjs;
	
	question_errors = question_errors + qhelper.errors
	
	if len(question_errors) > 0:
		opData = {'CSS':qcss,'XHTML':xhtml,'progressInfo':step,'questionEnd':questionEnd,'results':results,'resources':genfiles,'errors':question_errors}
		qlog.logu(str(question_errors))
	else:
		opData = {'CSS':qcss,'XHTML':xhtml,'progressInfo':step,'questionEnd':questionEnd,'results':results,'resources':genfiles}
	
	return jsonify(opData)