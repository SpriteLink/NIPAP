from nipapwww.tests import *

class TestXhrController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='xhr', action='index'))
        # Test response...
