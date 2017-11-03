import base64
from Crypto.Cipher import AES # pycrypto
import flask
from flask import Blueprint,jsonify,request
import json
import mimetypes
mimetypes.init()
import os
import os.path

from ..config.qconfig import Config
from ..libs import parseblocks,qlog
from ..libs.qcache import SaveToCache
from ..libs.qhelper import Qhelper

qengine_start = Blueprint('qengine_start', __name__)
@qengine_start.route('/session',methods=['POST'])
def start():
	config = Config()
	qhelper = Qhelper()
	
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
	
	invalidData = False
	if 'questionBaseURL' not in data:
		invalidData = True
	elif 'questionVersion' not in data:
		invalidData = True
	elif 'questionID' not in data:
		invalidData = True
	elif 'initialParamNames' not in data:	
		invalidData = True
	elif 'initialParamValues' not in data:	
		invalidData = True
	
	params = dict(zip(data['initialParamNames'],data['initialParamValues']))
		
	if 'randomseed' not in params:
		invalidData = True
	
	if invalidData:
		nodata = {'error':'Missing key. The POST json must have questionID, questionVersion, questionBaseURL, randomseed'}
		return jsonify(nodata)
	
	if "cachedResources" in data:
		cachedresources = data["cachedResources"]
	else:
		cachedresources = []
	
	# check pass key if set	
	if config.QENGINE_PASSKEY != None:
		if 'passKey' not in params:
			return jsonify({'error':'passkey is required'})
		presult = qhelper.checkPassKey(params['passKey'])
		if presult == 1:
			return jsonify({'error':'passkey is required'})
		elif presult == 2:
			return jsonify({'error':'invalid passkey format'})
		elif presult == 3:
			return jsonify({'error':'invalid passkey'})
	
	# grab optional variables
	if "language" not in params:
		params["language"] = None
	
	### OPEN & PARSE QUESTION ###
	
	qbasepath = "./questions/" + data['questionBaseURL'] + "/" + data['questionID'] + "/"
	
	# grab the question file, possibly from language file if available
	langfilefound= False
	if params["language"] is not None:
		qpath = qbasepath + data['questionVersion'] + params["language"]
		langfile = qhelper.get_first_file(qpath + "/question")
		if langfile is not None:
			qfile = langfile
			langfilefound= True
			langfolder = "/" + params["language"]
	
	if not langfilefound:
		qpath = qbasepath + data['questionVersion']
		qfile = qhelper.get_first_file(qpath + "/question")
		langfolder = ''
	
	if qfile is None:
		badfile = {'error':'The question you requested does not exist'}
		return flask.make_response(jsonify(badfile), 404)
	
	# create the question session ID, should be path to cache
	qsessionID = data['questionBaseURL'] + "/" + data['questionID'] + "/" + str(data['questionVersion']) + langfolder + "/" + str(params['randomseed'])
	
	fileblocks = parseblocks.Blocks()
	fileblocks.parseFile(qfile,0)
	
	if(len(fileblocks.errors) > 0):
		question_errors = question_errors + fileblocks.errors

	### GET BLOCKS & REQUESTED VARS ###

	#
	# important concepts:
	#	reqvars: holds all variables a block has requested
	#	qenginevars: holds all requested variables with produced values
	#	genfiles: holds all requested file resources
	
	# all requested variables in each block are loaded into this
	reqvars = {}
	
	# after a requested variable has gotten a value, it goes into this so it can be substituted into a block
	qenginevars = {'qengine':{}}
	for key in params:
		qenginevars['qengine'][key] = [params[key]]
	
	# all requested resources go into this
	genfiles = []
	
	# get all requested variables here
	for key in fileblocks.blocks:
		# add block conditionals to reqvars
		if fileblocks.blocks[key][2] is not None:
			reqvars = qhelper.add_to_reqvars(fileblocks.blocks[key][2],reqvars)
		
		# add qstore vars to reqvars
		if fileblocks.blocks[key][0] == 'qstore':
			reqvars = qhelper.get_qstore_vars(fileblocks.blocks[key][1],reqvars)
			continue
		
		# search any block for vars and add to reqvars
		reqvars = qhelper.get_reqvars(fileblocks.blocks[key][1],reqvars)
	
	### CREATE OR USE CACHE ###
	
	# create cache based on question session ID or check if it exists
	existingQSID = False
	sessionDataDir = config.QENGINE_CACHE_DIR + '/sessions/' + qsessionID
	sessionDataPath = sessionDataDir + '/0.json'
	if config.QENGINE_NO_CACHE == True:
		pass
	elif not os.path.exists(sessionDataDir):
		os.makedirs(sessionDataDir)
	else:
		existingQSID = True
		with open(sessionDataPath,"r") as jsonfile:
			sessionData = json.loads(jsonfile.read())
	
	# attempt to get variables & files from cache, 
	# we could just copy 0.json file to final vars, but the question may have changed
	if existingQSID:
		cachedvars = {}
		cachedfiles = []
		for key, val in reqvars.iteritems():
			cachedvars[key] = {}
			for var in val:
				try:
					if var[0] != '_':
						cachedvars[key][var] = sessionData[key][var]
					else:
						cachedvars[key][var] = sessionData[key][var]
						filename = cachedvars[key][var][0]
						if filename.split('.')[0] != 'error' and filename not in cachedresources:
							with open(sessionDataDir + '/' + cachedvars[key][var][0],"r") as file:
								mt = mimetypes.guess_type(filename)[0]
								cachedfiles.append({
										"content" : base64.b64encode(file.read()),
										"encoding" : "base64",
										"filename" : filename,
										"mimeType" : mt,
									})
				except Exception as e:
					# key error, something cached is not available, so just run it all again
					existingQSID = False
	
	# if cache was successful, set qenginevars to cachedvars
	if existingQSID:
		qenginevars = cachedvars
		genfiles = cachedfiles
	
	### PROCESS BLOCKS ###
	
	# block: qcss
	qcss = ''
	# block: qhtml
	qhtml = ''
	# block: qstore
	vhtml = ''
	
	# grab content from different blocks, add reqvars, and get any requested files if cache didn't work
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
			elif fileblocks.blocks[key][0] == 'qhtml':
				qhtml += qhelper.substitute_vars(qhelper.substitute_shortcodes(fileblocks.blocks[key][1],qenginevars),qenginevars)
			elif fileblocks.blocks[key][0] == 'qstore':
				vhtml += qhelper.store_vars_in_html(fileblocks.blocks[key][1],qenginevars,config.QENGINE_SALT,config.QENGINE_IV)
			elif fileblocks.blocks[key][0] in config.BLOCKS:
				if not existingQSID:
					try:
						subblock = qhelper.substitute_vars(fileblocks.blocks[key][1],qenginevars)
						config.BLOCKS[fileblocks.blocks[key][0]](key,subblock,reqvars,qenginevars,cachedresources,genfiles,question_errors)
					except Exception as e:
						qlog.loge(str(e) + ' blocktype: ' + fileblocks.blocks[key][0])
	
	### SAVE DATA TO CACHE ###
	
	# write data to cache
	if config.QENGINE_NO_CACHE == False:
		cachethread = SaveToCache(qenginevars, genfiles, sessionDataPath, sessionDataDir)
		cachethread.start()
	
	### FINAL RESPONSE ASSEMBLY ###
	
	aesObj = AES.new(config.QENGINE_SALT, AES.MODE_CFB, config.QENGINE_IV)
	stephtml = "<input type='hidden' name='%%IDPREFIX%%temp.qengine.step' value='" + base64.b64encode(aesObj.encrypt('0')) + "'>"
	
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
	
	xhtml = qhtml + vhtml + stephtml + mjaxjs
	
	question_errors = question_errors + qhelper.errors
	
	# assemble the final json response. progressInfo is set to the step number, so in this case it's 0, and process() will increment this
	if len(question_errors) > 0:
		opData = {'CSS':qcss,'XHTML':xhtml,'progressInfo':0,'questionSession':qsessionID,'resources':genfiles,'errors':question_errors}
		qlog.logu(str(question_errors))
	else:
		opData = {'CSS':qcss,'XHTML':xhtml,'progressInfo':0,'questionSession':qsessionID,'resources':genfiles}
	
	return jsonify(opData)