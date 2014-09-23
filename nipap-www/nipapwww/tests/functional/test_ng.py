from nipapwww.tests import *

class TestNgController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='ng', action='index'))
        # Test response...
