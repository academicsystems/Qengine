import flask
from flask import Blueprint,jsonify,request
import os.path
import urllib
import yaml # pyyaml

from ..config import config
from ..libs.qhelper import Qhelper

qengine_qmetadata = Blueprint('qengine_qmetadata', __name__)
@qengine_qmetadata.route('/question/<string:base>/<string:id>/<string:version>',methods=['GET'])
def getQuestionMetadata(base,id,version):
	
	qhelper = Qhelper({'MOODLE_HACK':config.QENGINE_MOODLE_HACKS})
	
	# check pass key if set
	if config.QENGINE_PASSKEY != None:
		passKey = request.args.get('passKey')
		if passKey is None:
			noaccess = {'error':'passkey is required'}
			return jsonify(noaccess)
		else:
			if not qhelper.checkPassKey(passKey):
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