import flask
from flask import Blueprint,jsonify,request
import os.path
import urllib

from ..config.qconfig import Config
from ..libs.qhelper import Qhelper
from ..libs.qio import Qio

qengine_qmetadata = Blueprint('qengine_qmetadata', __name__)
@qengine_qmetadata.route('/question/<string:base>/<string:id>/<string:version>',methods=['GET'])
def getQuestionMetadata(base,id,version):
	
	config = Config()
	qhelper = Qhelper()
	qio = Qio()
	
	# check pass key if set	
	if config.QENGINE_PASSKEY != None:
		presult = qhelper.checkPassKey(request.args.get('passKey'))
		if presult == 1:
			return jsonify({'error':'passkey is required'})
		elif presult == 2:
			return jsonify({'error':'invalid passkey format'})
		elif presult == 3:
			return jsonify({'error':'invalid passkey'})
	
	base = urllib.unquote(base)
	id = urllib.unquote(id)
	version = urllib.unquote(version)
	
	# check that question file exists first
	if qio.getQuestion(base,id,version) == False:
		badfile = {'error':'The question you requested does not exist'}
		return flask.make_response(jsonify(badfile), 404)
	
	# get metadata
	md = qio.getMetadata(base,id)
	if md == False:
		nometadata = {'questionmetadata':'none'}
		return jsonify(nometadata)
	else:
		return jsonify({'questionmetadata':md})
	