import flask
from flask import Blueprint,jsonify,request
import os.path
import shutil
import time
import urllib
import yaml # pyyaml

from ..config.qconfig import Config
from ..libs import parseblocks,qlog
from ..libs.qhelper import Qhelper
from ..libs.qio import Qio

qengine_create = Blueprint('qengine_create', __name__)
@qengine_create.route('/question/<string:base>/<string:id>/<string:version>',methods=['POST'])
def postQuestionFile(base,id,version):
	
	config = Config()
	qhelper = Qhelper()
	qio = Qio()
	
	# check if posting question files is enabled on this engine
	if config.QENGINE_ENABLE_REMOTE != True:
		notallowed = {'error':'This Qengine does not accept posting question files.'}
		return jsonify(notallowed)
	
	### INCOMING DATA ###

	data = flask.request.get_json()
	if data is None:
		try:
			data = json.loads(flask.request.data)
		except:
			nodata = {'error':'No json body detected or unable to parse request body'}
			return jsonify(nodata)
	
	# check pass key if set
	if config.QENGINE_PASSKEY != None:
		if 'passKey' not in data:
			return jsonify({'error':'passkey is required'})
		presult = qhelper.checkPassKey(data['passKey'])
		if presult == 1:
			return jsonify({'error':'passkey is required'})
		elif presult == 2:
			return jsonify({'error':'invalid passkey format'})
		elif presult == 3:
			return jsonify({'error':'invalid passkey'})
	
	# validate data
	if 'questionFile' not in data:
		error= {'error':'Missing questionFile in JSON'}
		return jsonify(error)
	else:
		# remove carriage returns from data
		questionFile = data['questionFile'].replace("\r",'')
	
	# check for errors in file
	allblocks = parseblocks.Blocks()
	allblocks.parseAllSteps(questionFile)
	
	if(len(allblocks.errors) > 0):
		return jsonify({'error':allblocks.errors})
	
	base = urllib.unquote(base)
	id = urllib.unquote(id)
	version = urllib.unquote(version)
	
	# make question dir if not exists or create back up of old question file
	wresult = qio.setQuestion(base,id,version,questionFile,True)
	
	if wresult == False:
		error= {'error':'Unable to write question file'}
		return jsonify(error)
	
	# check for a block to write question metadata
	fileblocks = parseblocks.Blocks()
	fileblocks.parseString(questionFile,0)
	
	for key in fileblocks.order:
		if fileblocks.blocks[key][0] == 'qmetadata':
			wresult = qio.setMetadata(base,id,fileblocks.blocks[key][1])
			if wresult == False:
				error= {'error':'Question file was written, but metadata could not be updated'}
				return jsonify(error)
	
	# if metadata does not exist, make blank metadata file
	if not qio.getMetadata(base,id):
		qio.setMetadata(base,id,'')
		if mresult == False:
			error= {'error':'Question file was written, but blank metadata file could not be created'}
			return jsonify(error)
		
	
	return jsonify({'result':'ok'})
	
