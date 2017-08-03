#!/usr/bin/python2.7

from flup.server.fcgi import WSGIServer
from qengine import app

if __name__ == '__main__':
	WSGIServer(app).run()