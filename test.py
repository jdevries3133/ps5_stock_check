from types import SimpleNamespace
from unittest import TestCase

from main import Result, send_webhook_message, CheckStock

class TestMain(TestCase):
    """
    These are not real unit tests, but they run all the code to see if
    there are bugs, bring me up to debugging breakpoints, and I can add
    assertions here or there if possible.
    """


    def setUp(self):
        self.checker = CheckStock()

    def tearDown(self):
        self.checker.session.close()

    def test_send_webhook_message(self):
        """
        This sends a *real* web hook message.
        Uncomment for test suite spam
        """
        res = send_webhook_message('Hello, world! The webhook link works.')
        self.assertIn(res.status_code, range(200, 300))

    def test_walmart(self ):
        result = self.checker.check_walmart()
        self.assertIsInstance(result, Result)

    def test_sony(self):
        result = self.checker.check_sony()
        self.assertIsInstance(result, Result)

    def test_bestbuy(self):
        result = self.checker.check_bestbuy()
        self.assertIsInstance(result, Result)
