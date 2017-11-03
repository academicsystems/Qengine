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

qengine_create = Blueprint('qengine_create', __name__)
@qengine_create.route('/question/<string:base>/<string:id>/<string:version>',methods=['POST'])
def postQuestionFile(base,id,version):
	
	config = Config()
	qhelper = Qhelper()
	
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
		return jsonify({'errors':allblocks.errors})
	
	# create or update question
	basepath = qdirname = "./questions/" + urllib.unquote(base) + "/" + urllib.unquote(id) + "/";
	metafilepath = basepath + "metadata"
	qdirname = basepath + urllib.unquote(version)
	qfilepath = qdirname + "/" + "question"
	
	# make question dir if not exists or create back up of old question file
	if not os.path.isdir(qdirname):
		os.makedirs(qdirname,0750)
	elif os.path.isfile(qfilepath):
		stamp = str(time.time())
		shutil.move(qfilepath,stamp + "_backup")
		
	with open(qfilepath,'wb') as file:
		file.write("%s" % questionFile)
		
	fileblocks = parseblocks.Blocks()
	fileblocks.parseFile(qfilepath,0)
	
	# check for a block to write question metadata
	for key in fileblocks.order:
		if fileblocks.blocks[key][0] == 'qmetadata':
			with open(metafilepath,'wb') as file:
				file.write("%s" % fileblocks.blocks[key][1])
	
	# if metadata does not exist, make blank metadata file
	if not os.path.isdir(metafilepath):
		open(metafilepath,'a').close()
	
	return jsonify({'result':'ok'})
	
