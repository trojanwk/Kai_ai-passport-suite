"""Slow full-state reads must not hide successful authenticated companion traffic."""
import sys
import threading
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from passport_device import Device

class LinkHealthTests(TestCase):
    def device(self):
        device=Device.__new__(Device)
        device.state={'transport':'ble'};device.lock=threading.Lock();device.transport='ble'
        device.last_seen=80;device.last_contact=99
        device.token='placeholder';device.radio=Mock()
        return device

    def test_recent_heartbeat_keeps_link_ready_while_status_age_remains_accurate(self):
        with patch('passport_device.time.monotonic',return_value=100):state=self.device().snapshot()
        self.assertTrue(state['link_ready']);self.assertEqual(state['status_age_seconds'],20)
        self.assertEqual(state['contact_age_seconds'],1)

    def test_stale_contact_still_reports_disconnected(self):
        device=self.device();device.last_contact=85
        with patch('passport_device.time.monotonic',return_value=100):self.assertFalse(device.snapshot()['link_ready'])

    def test_transport_change_requires_a_status_from_the_new_transport(self):
        device=self.device();device.transport='usb'
        with patch('passport_device.time.monotonic',return_value=100):self.assertFalse(device.snapshot()['link_ready'])

    def test_successful_request_refreshes_contact(self):
        device=self.device();device.radio.request.return_value={'ok':True}
        with patch('passport_device.time.monotonic',return_value=100):self.assertEqual(device.request('/events'),{'ok':True})
        self.assertEqual(device.last_contact,100);self.assertEqual(device.last_seen,80)

    def test_failed_request_does_not_refresh_contact(self):
        device=self.device();device.radio.request.side_effect=ConnectionError()
        with self.assertRaises(ConnectionError):device.request('/events')
        self.assertEqual(device.last_contact,99)
