"""A page change reuses notifications; a real disconnect requires fresh subscriptions."""
import asyncio
import collections
import sys
import threading
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from passport_device import Radio,KEY,AUDIO

class Client:
    def __init__(self):
        self.is_connected=True
        self.start_notify=AsyncMock()
        self.stop_notify=AsyncMock()

class RadioSubscriptionTests(IsolatedAsyncioTestCase):
    def radio(self):
        radio=Radio.__new__(Radio)
        radio.client=Client();radio.voice_client=None;radio.voice_lock=asyncio.Lock()
        radio.events=collections.deque(maxlen=1024);radio.lock=threading.Lock();radio.dropped=0
        return radio

    async def test_reentry_reuses_notifications_and_flushes_old_page_reports(self):
        radio=self.radio()
        first=await radio.call('voice_subscribe',{})
        radio.notify(2,b'old page');radio.dropped=3
        second=await radio.call('voice_subscribe',{})
        self.assertFalse(first['result']['reused']);self.assertTrue(second['result']['reused'])
        self.assertEqual(radio.client.start_notify.await_count,2)
        radio.client.stop_notify.assert_not_awaited()
        self.assertEqual(list(radio.events),[]);self.assertEqual(radio.dropped,0)

    async def test_disconnect_invalidates_subscriptions_and_old_callback_cannot_break_new_link(self):
        radio=self.radio();await radio.call('voice_subscribe',{})
        old=radio.client;radio.disconnected(old)
        self.assertIsNone(radio.voice_client);self.assertEqual(radio.events[-1]['report'],0)
        radio.client=Client();await radio.call('voice_subscribe',{})
        radio.disconnected(old)
        self.assertIs(radio.voice_client,radio.client)
        self.assertEqual(list(radio.events),[])
        self.assertEqual(radio.client.start_notify.await_count,2)

    async def test_partial_failure_is_cleaned_up_and_next_attempt_can_succeed(self):
        radio=self.radio();radio.client.start_notify.side_effect=[None,RuntimeError('transient failure')]
        with self.assertRaises(RuntimeError):await radio.call('voice_subscribe',{})
        self.assertIsNone(radio.voice_client)
        radio.client.stop_notify.assert_awaited_once_with(KEY)
        radio.client.start_notify.side_effect=None
        result=await radio.call('voice_subscribe',{})
        self.assertFalse(result['result']['reused']);self.assertIs(radio.voice_client,radio.client)

    async def test_parallel_reentry_registers_only_once(self):
        radio=self.radio()
        await asyncio.gather(radio.call('voice_subscribe',{}),radio.call('voice_subscribe',{}))
        self.assertEqual(radio.client.start_notify.await_count,2)

    async def test_disconnected_client_never_reuses_the_cached_subscription(self):
        radio=self.radio();await radio.call('voice_subscribe',{})
        radio.client.is_connected=False
        with self.assertRaises(ConnectionError):await radio.call('voice_subscribe',{})
