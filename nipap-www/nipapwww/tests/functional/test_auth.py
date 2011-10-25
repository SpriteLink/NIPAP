from nipapwww.tests import *

class TestAuthController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='login', action='index'))
        # Test response...
