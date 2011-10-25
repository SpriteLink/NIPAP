from nipapwww.tests import *

class TestPoolController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='pool', action='index'))
        # Test response...
