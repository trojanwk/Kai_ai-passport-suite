"""Renaming a paired badge must not redirect the companion to another badge."""
import sys
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import TestCase

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from passport_assistant import validate_config
from passport_device import matches_passport,SERVICE

IDENTIFIER='12345678-1234-4234-8234-123456789abc'
EXPECTED='AI-Passport-102030405060'

class BluetoothIdentityTests(TestCase):
    def test_pinned_device_can_be_renamed_but_another_badge_is_rejected(self):
        advertisement=NS(local_name='Renamed badge',service_uuids=[SERVICE])
        self.assertTrue(matches_passport(NS(address=IDENTIFIER.upper()),advertisement,EXPECTED,IDENTIFIER))
        advertisement.local_name=EXPECTED
        self.assertFalse(matches_passport(NS(address='another-device'),advertisement,EXPECTED,IDENTIFIER))

    def test_pinned_identifier_still_requires_the_companion_service(self):
        self.assertFalse(matches_passport(NS(address=IDENTIFIER),NS(local_name=EXPECTED,service_uuids=['1812']),EXPECTED,IDENTIFIER))

    def test_existing_pairings_keep_exact_name_matching(self):
        device=NS(address=IDENTIFIER)
        self.assertTrue(matches_passport(device,NS(local_name=EXPECTED,service_uuids=[SERVICE.upper()]),EXPECTED))
        self.assertFalse(matches_passport(device,NS(local_name='Other badge',service_uuids=[SERVICE]),EXPECTED))

    def test_saved_identifier_is_validated_and_preserved(self):
        config={'mac':'10:20:30:40:50:60','api_token':'a'*64,'bluetooth_id':IDENTIFIER.upper()}
        self.assertEqual(validate_config(config)['bluetooth_id'],IDENTIFIER)
        for value in ('arbitrary-name',None,123):
            with self.assertRaises(ValueError):validate_config(dict(config,bluetooth_id=value))
