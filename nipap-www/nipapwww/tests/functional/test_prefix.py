from nipapwww.tests import *

class TestPrefixController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='prefix', action='index'))
        # Test response...
