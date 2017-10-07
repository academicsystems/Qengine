from flask import Blueprint,jsonify,request

from ..config.qconfig import Config
from ..libs.qhelper import Qhelper

qengine_einfo = Blueprint('qengine_einfo', __name__)
@qengine_einfo.route('/info',methods=['GET'])
def getEngineInfo():
	
	config = Config()
	qhelper = Qhelper()
	
	# check pass key if set	
	if config.QENGINE_PASSKEY != None:
		presult = qhelper.checkPassKey(request.args.get('passKey'))
		if presult == 1:
			return jsonify({'error':'passkey is required'})
		elif presult == 2:
			return jsonify({'error':'invalid passkey format'})
		elif presult == 3:
			return jsonify({'error':'invalid passkey'})
	
	engineinfo = {'engineinfo':config.ENGINEINFO}
	return jsonify(engineinfo)