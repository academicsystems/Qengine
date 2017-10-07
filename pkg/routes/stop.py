import flask
from flask import Blueprint,jsonify
import urllib
import shutil

from ..config.qconfig import Config
from ..libs.qhelper import Qhelper

qengine_stop = Blueprint('qengine_stop', __name__)
@qengine_stop.route('/session/<path:sid>',methods=['DELETE'])
def stop(sid):
	config = Config()
	
	# check pass key if set	
	if config.QENGINE_PASSKEY != None:
		presult = qhelper.checkPassKey(request.args.get('passKey'))
		if presult == 1:
			return jsonify({'error':'passkey is required'})
		elif presult == 2:
			return jsonify({'error':'invalid passkey format'})
		elif presult == 3:
			return jsonify({'error':'invalid passkey'})
	
	# this might indicate hack attempt, as .. should never be in path
	if '..' in sid or '~/' in sid:
		return flask.make_response('',400)
	
	sessionPath = config.QENGINE_CACHE_DIR + '/sessions/' + urllib.unquote(sid)
	shutil.rmtree(sessionPath, ignore_errors=True)
	
	return ''