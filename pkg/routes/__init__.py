# public imports
import flask
from flask import Flask
from flask import request

# private imports
from ..config.qconfig import Config

config = Config()
if not config.initialized:
	config.init(None)

app = Flask(__name__)

# route hooks
@app.before_request
def log_request():
	if config.QENGINE_LOG_REQUESTS:
		with open('./logs/request.log','a+') as file:
			file.write("%s %s\n%s%s\n\n" % (request.method, request.url, request.headers, request.get_json(silent=True)))
	return None

# import routes
from pkg.routes.getEngineInfo import qengine_einfo
from pkg.routes.getQuestionMetadata import qengine_qmetadata
from pkg.routes.start import qengine_start
from pkg.routes.process import qengine_process
from pkg.routes.stop import qengine_stop

# register route blueprints
app.register_blueprint(qengine_einfo)
app.register_blueprint(qengine_qmetadata)
app.register_blueprint(qengine_start)
app.register_blueprint(qengine_process)
app.register_blueprint(qengine_stop)

# catch all routes
@app.route('/<path:badpath>')
def fallback(badpath):
	return flask.make_response('Path Not Found', 404)