from werkzeug.wrappers import Request
from flask import session
import time


class UpdateToken(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)
        # if 'expiration' in session and session['expiration'] - time.time() < 900:
        #     self.refresh_token()
        # for cookie in request.cookies:
        #     print(cookie, type(cookie))
        return self.app(environ, start_response)

    def refresh_token(self):
        pass
