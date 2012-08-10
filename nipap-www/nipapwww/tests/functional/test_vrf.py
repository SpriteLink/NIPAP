from nipapwww.tests import *

class TestVrfController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='vrf', action='index'))
        # Test response...
