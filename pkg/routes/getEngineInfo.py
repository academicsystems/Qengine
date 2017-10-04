from flask import Blueprint,jsonify,request

from ..config import config
from ..libs.qhelper import Qhelper

qengine_einfo = Blueprint('qengine_einfo', __name__)
@qengine_einfo.route('/info',methods=['GET'])
def getEngineInfo():
	
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
	
	engineinfo = {'engineinfo':config.ENGINEINFO}
	return jsonify(engineinfo)