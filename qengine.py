#!/usr/bin/python2.7

# include blocks/ directory
import sys
sys.path.insert(0, './blocks')
sys.path.insert(0, './libs')

# public imports
import base64
from Crypto.Cipher import AES # pycrypto
import flask
from flask import Flask
from flask import jsonify
from flask import request
import hashlib
import json
import mimetypes
mimetypes.init()
import os
import os.path
from random import choice
import re
import requests
import urllib
import shutil
from string import ascii_uppercase
import threading
import yaml # pyyaml

# private imports
import parseblocks
import loadblocks as lb
import qhelper

# start up & load configuration

def log(message):
	with open('./qlog.txt','a+') as file:
		file.write("%s\n\n" % message)

def loadConfigOption(key,default,configuration):
	try:
		value = configuration[key]
		if type(value) is str:
			if len(value) == 0:
				value = default
	except:
		value = default
	
	return value

with open('./configuration.yaml','r') as f:
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
	QENGINE_LOG_REQUESTS = loadConfigOption('QENGINE_LOG_REQUESTS',False,configuration)
	QENGINE_MOODLE_HACKS = loadConfigOption('QENGINE_MOODLE_HACKS',False,configuration)
	QENGINE_NO_CACHE = loadConfigOption('QENGINE_NO_CACHE',False,configuration)
	QENGINE_PASSKEY = loadConfigOption('QENGINE_PASSKEY',None,configuration)
	
	ENGINEINFO = {}
	
	# engine info
	for key in configuration:
		if 'ENGINEINFO_' in key:
			ekey = key.split('_',1)[1]
			if len(ekey) > 0:
				ENGINEINFO[ekey] = configuration[key]
	
	BLOCKS = lb.loadblocks(configuration)

app = Flask(__name__)

# helper functions

def checkPassKey(enciv):
	encivArray = enciv.split(':')
	if len(encivArray) != 2:
		return False
	aesObj = AES.new(hashlib.md5(QENGINE_PASSKEY).hexdigest(), AES.MODE_CFB, encivArray[1], segment_size=8)
	pkmessage = aesObj.decrypt(base64.b64decode(encivArray[0]))
			
	if pkmessage != 'success':
		return False
	
	return True

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

# routes

@app.before_request
def log_request():
	if QENGINE_LOG_REQUESTS:
		with open('./qlog.txt','a+') as file:
			file.write("%s %s\n%s%s\n\n" % (request.method, request.url, request.headers, request.get_json(silent=True)))
	return None

@app.route('/info',methods=['GET'])
def getEngineInfo():
	# check pass key if set
	if QENGINE_PASSKEY != None:
		passKey = request.args.get('passKey')
		if passKey is None:
			noaccess = {'error':'passkey is required'}
			return jsonify(noaccess)
		else:
			if not checkPassKey(passKey):
				noaccess = {'error':'invalid passkey'}
				return jsonify(noaccess)
	
	engineinfo = {'engineinfo':ENGINEINFO}
	return jsonify(engineinfo)

@app.route('/question/<string:base>/<string:id>/<string:version>',methods=['GET'])
def getQuestionMetadata(base,id,version):
	# check pass key if set
	if QENGINE_PASSKEY != None:
		passKey = request.args.get('passKey')
		if passKey is None:
			noaccess = {'error':'passkey is required'}
			return jsonify(noaccess)
		else:
			if not checkPassKey(passKey):
				noaccess = {'error':'invalid passkey'}
				return jsonify(noaccess)
	
	qdirname = "./questions/" + urllib.unquote(base) + "/" + urllib.unquote(id) + "/" + urllib.unquote(version)
	
	if not os.path.isdir(qdirname):
		badfile = {'error':'The question you requested does not exist'}
		return flask.make_response(jsonify(badfile), 404)
	try:
		metadatafile = "./questions/" + base + "/" + id + "/" + "metadata"
		file = qhelper.get_first_file(metadatafile)
		if file is not None:
			with open(file,'r') as f:
				metadata = yaml.load(f.read())
				return jsonify({'questionmetadata':metadata})
		else:
			nometadata = {'questionmetadata':'none'}
			return jsonify(nometadata)
	except:
		nometadata = {'questionmetadata':'none'}
		return jsonify(nometadata)

@app.route('/session',methods=['POST'])
def start():
	
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
	if QENGINE_PASSKEY != None:
		if "passKey" not in params:
			noaccess = {'error':'passkey is required'}
			return jsonify(noaccess)
		else:
			m = hashlib.md5()
			m.update(QENGINE_PASSKEY)
			m.digest()
			if params["passKey"] != m.hexdigest():
				noaccess = {'error':'invalid passkey'}
				return jsonify(noaccess)
	
	# grab optional variables
	if "language" not in params:
		params["language"] = None
	
	# ignored variables, could be useful later:
	if "userid" not in params:
		params["userid"] = None
	if "preferredbehaviour" not in params:
		params["preferredbehaviour"] = None
	if "attempt" not in params:
		params["attempt"] = None # don't be fooled, is actually just a random number used by OpenMark as randomseed
	if "navigatorVersion" not in params:
		params["navigatorVersion"] = None
	if "display_readonly" not in params:
		params["display_readonly"] = None
	if "display_marks" not in params:
		params["display_marks"] = None
	if "display_markdp" not in params:
		params["display_markdp"] = None
	if "display_correctness" not in params:
		params["display_correctness"] = None
	if "display_feedback" not in params:
		params["display_feedback"] = None
	if "display_generalfeedback" not in params:
		params["display_generalfeedback"] = None
	
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
		# check block for conditional
		if fileblocks.blocks[key][2] is not None:
			reqvars = qhelper.add_to_reqvars(fileblocks.blocks[key][2],reqvars)
		
		# grab vars from html & put in reqvars by namespace
		reqvars = qhelper.get_reqvars(fileblocks.blocks[key][1],reqvars)
		if reqvars is None:
			badfile = {'error':'invalid variable name in block, must be: blockname.name'}
			return flask.make_response(jsonify(badfile), 404)
	
	### CREATE OR USE CACHE ###
	
	# create cache based on question session ID or check if it exists
	existingQSID = False
	sessionDataDir = QENGINE_CACHE_DIR + '/sessions/' + qsessionID
	sessionDataPath = sessionDataDir + '/0.json'
	if QENGINE_NO_CACHE == True:
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
				qhelper.get_local_files(fileblocks.blocks[key][1],qpath,genfiles)
			elif fileblocks.blocks[key][0] == 'qhtml':
				qhtml += qhelper.substitute_vars(qhelper.substitute_shortcodes(fileblocks.blocks[key][1]),qenginevars)
			elif fileblocks.blocks[key][0] == 'qstore':
				vhtml += qhelper.store_vars_in_html(fileblocks.blocks[key][1],qenginevars,QENGINE_SALT,QENGINE_IV)
			elif fileblocks.blocks[key][0] in BLOCKS:
				if not existingQSID:
					BLOCKS[fileblocks.blocks[key][0]](key,fileblocks.blocks[key][1],reqvars,qenginevars,cachedresources,genfiles)
	
	### SAVE DATA TO CACHE ###
	
	# write data to cache
	if QENGINE_NO_CACHE == False:
		cachethread = SaveToCache(qenginevars, genfiles, sessionDataPath, sessionDataDir)
		cachethread.start()
	
	### FINAL RESPONSE ASSEMBLY ###
	
	aesObj = AES.new(QENGINE_SALT, AES.MODE_CFB, QENGINE_IV)
	stephtml = "<input type='hidden' name='%%IDPREFIX%%temp.qengine.step' value='" + base64.b64encode(aesObj.encrypt('0')) + "'>"
	
	# assemble the final json response. progressInfo is set to the step number, so in this case it's 0, and process() will increment this
	opData = {'CSS':qcss,'XHTML':qhtml + vhtml + stephtml,'progressInfo':0,'questionSession':qsessionID,'resources':genfiles}
	
	return jsonify(opData)

@app.route('/session/<path:sid>',methods=['POST'])
def process(sid):
	
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
			aesObj = AES.new(QENGINE_SALT, AES.MODE_CFB, QENGINE_IV)
			if QENGINE_MOODLE_HACKS:
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
		log(str(e))
	
	# parse next step in question
	step = int(qenginevars['qengine']['step'][0]) + 1
	
	# get path to question from sid: base/questionID/questionVersion/(language)/randomseed
	pathList = sid.split('/')
	
	randomseed = pathList[-1]
	del pathList[-1]
	
	qfile = qhelper.get_first_file('./questions/' + '/'.join(pathList) + '/question')
	
	fileblocks = parseblocks.Blocks()
	fileblocks.parseFile(qfile,step)
	
	### GET REQUESTED VARIABLES ###
	
	reqvars = {}
	genfiles = []
	
	# get all requested variables here
	for key in fileblocks.blocks:
		# check block for conditional
		if fileblocks.blocks[key][2] is not None:
			reqvars = qhelper.add_to_reqvars(fileblocks.blocks[key][2],reqvars)
		
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
				qhelper.get_local_files(fileblocks.blocks[key][1],qpath,genfiles)
			elif fileblocks.blocks[key][0] == 'qans':
				try:
					resvar = qhelper.get_stubs('@@',fileblocks.blocks[key][1])[-1]
					resparts = resvar.split('.')
					result = float(qenginevars[resparts[0]][resparts[1]][0])
				except:
					result = 0
			elif fileblocks.blocks[key][0] == 'qhtml':
				qhtml += qhelper.substitute_vars(qhelper.substitute_shortcodes(fileblocks.blocks[key][1]),qenginevars)
			elif fileblocks.blocks[key][0] == 'qstore':
				vhtml += qhelper.store_vars_in_html(fileblocks.blocks[key][1],qenginevars,QENGINE_SALT,QENGINE_IV)
			elif fileblocks.blocks[key][0] in BLOCKS:
					BLOCKS[fileblocks.blocks[key][0]](key,fileblocks.blocks[key][1],reqvars,qenginevars,cachedresources,genfiles)
	
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
	
	aesObj = AES.new(QENGINE_SALT, AES.MODE_CFB, QENGINE_IV)
	stephtml = "<input type='hidden' name='%%IDPREFIX%%temp.qengine.step' value='" + base64.b64encode(aesObj.encrypt(str(step))) + "'>"
	
	opData = {'CSS':qcss,'XHTML':qhtml + vhtml + stephtml,'progressInfo':step,'questionEnd':questionEnd,'results':results,'resources':genfiles}
	
	return jsonify(opData)

@app.route('/session/<path:sid>',methods=['DELETE'])
def stop(sid):
	# this might indicate hack attempt, as .. should never be in path
	if '..' in sid or '~/' in sid:
		return ''
	
	sessionPath = QENGINE_CACHE_DIR + '/sessions/' + urllib.unquote(sid)
	shutil.rmtree(sessionPath, ignore_errors=True)
	
	return ''

@app.route('/<path:badpath>')
def fallback(badpath):
	return flask.make_response('Path Not Found', 404)
	
if __name__ == '__main__':
	app.run()

