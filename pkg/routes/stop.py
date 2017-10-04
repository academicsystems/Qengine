from flask import Blueprint,jsonify
import urllib
import shutil

from ..config import config
from ..libs.qhelper import Qhelper

qengine_stop = Blueprint('qengine_stop', __name__)
@qengine_stop.route('/session/<path:sid>',methods=['DELETE'])
def stop(sid):
	# this might indicate hack attempt, as .. should never be in path
	if '..' in sid or '~/' in sid:
		return ''
	
	sessionPath = config.QENGINE_CACHE_DIR + '/sessions/' + urllib.unquote(sid)
	shutil.rmtree(sessionPath, ignore_errors=True)
	
	return ''