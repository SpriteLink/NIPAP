from nipapwww.tests import *

class TestSchemaController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='schema', action='index'))
        # Test response...
