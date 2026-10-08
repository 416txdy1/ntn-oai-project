"""单调时钟 ICMP 编解码回归，不需要网络权限。"""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('monotonic_ping',Path(__file__).with_name('monotonic_ping.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class MonotonicPingTests(unittest.TestCase):
    def test_request_checksum_and_echo_payload(self):
        nonce=b'12345678'
        request=m.make_request(23,987654321,nonce)
        self.assertEqual(len(request),64)
        self.assertEqual(m.checksum(request),0)
        reply=bytes([0])+request[1:]
        self.assertEqual(m.parse_reply(reply,nonce),(23,987654321))

    def test_raw_ipv4_header_is_removed(self):
        nonce=b'12345678'
        reply=bytes([0])+m.make_request(2,300,nonce)[1:]
        packet=bytes([0x45])+bytes(19)+reply
        self.assertEqual(m.parse_reply(packet,nonce),(2,300))

    def test_unrelated_and_truncated_packets_rejected(self):
        nonce=b'12345678'
        packet=m.make_request(2,300,nonce)
        self.assertIsNone(m.parse_reply(packet,nonce))
        self.assertIsNone(m.parse_reply(bytes([0])+packet[1:],b'87654321'))
        self.assertIsNone(m.parse_reply(b'\x45',nonce))

if __name__=='__main__': unittest.main()
