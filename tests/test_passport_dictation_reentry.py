"""Recover transient channel setup failures without retrying permission errors or old pages."""
import sys
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from passport_services import Services

class DictationReentryTests(TestCase):
    def service(self,failures):
        service=Services.__new__(Services)
        service.active=service.requested_context=(2,7)
        service.dictation_ble=NS(open=Mock(side_effect=failures),status=Mock(return_value={'state':'ready'}))
        service.stop=NS(wait=Mock(return_value=False))
        return service

    def enter(self,service):
        return service.response({'app':2,'generation':7,'operation':'enter'})

    def test_transient_failure_retries_automatically_and_returns_ready(self):
        service=self.service([ConnectionError('reconnecting'),TimeoutError(),None])
        self.assertEqual(self.enter(service),{'state':'ready'})
        self.assertEqual(service.dictation_ble.open.call_count,3)

    def test_permission_failure_is_not_retried(self):
        service=self.service([PermissionError('needs permission')])
        with self.assertRaises(PermissionError):self.enter(service)
        self.assertEqual(service.dictation_ble.open.call_count,1)

    def test_retries_stop_when_user_leaves_the_page(self):
        service=self.service([ConnectionError('reconnecting')]);service.requested_context=(5,8)
        with self.assertRaises(ConnectionError):self.enter(service)
        self.assertEqual(service.dictation_ble.open.call_count,1)

    def test_persistent_failure_has_a_bounded_retry_count(self):
        service=self.service(ConnectionError('unavailable'))
        with self.assertRaises(ConnectionError):self.enter(service)
        self.assertEqual(service.dictation_ble.open.call_count,3)
