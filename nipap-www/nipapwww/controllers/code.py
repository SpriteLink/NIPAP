import uuid, logging
from pylons import session, request
from pylons.controllers.util import redirect
from nipap.nipapconfig import NipapConfig
from nipapwww.lib.base import BaseController

log = logging.getLogger(__name__)

class CodeController(BaseController):
    def index(self):
	cfg = NipapConfig()
	scope = 'openid%20' + cfg.get('www', 'scope')
        currentUrl = cfg.get('www', 'callbackUrl')
        state = str(uuid.uuid4()).replace('-', '')
        nonce = str(uuid.uuid4()).replace('-', '')
        session[state] = {
            'nonce': nonce,
            'redirect': currentUrl,
            'callback': cfg.get('www', 'callbackUrl')
        }
        url = (cfg.get('www', 'baseUrl') + 'authorize' +
            '?response_type=code' +
            '&client_id=' + cfg.get('www', 'client_id') +
            '&scope=' + scope +
            '&redirect_uri=' + cfg.get('www', 'callbackUrl') +
            '&state=' + state +
            '&nonce=' + nonce)
        redirect(url)

