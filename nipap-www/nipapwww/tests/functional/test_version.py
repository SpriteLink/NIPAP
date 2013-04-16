from nipapwww.tests import *

class TestVersionController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='version', action='index'))
        # Test response...
