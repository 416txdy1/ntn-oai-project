"""回归模板旧地址造成 SCTP bind 失败；不修改真实网络。"""
import subprocess
import unittest
from unittest.mock import patch
from network_config import configure, check_network, addresses

class NetworkTest(unittest.TestCase):
    def test_old_template_and_override(self):
        template = 'amf_ip_address = ({ ipv4 = "192.168.71.132"; });\nGNB_IPV4_ADDRESS_FOR_NG_AMF = "192.168.71.140/26";\nGNB_IPV4_ADDRESS_FOR_NGU = "192.168.71.140/26";'
        output = configure(template, {})
        self.assertIn('"192.168.70.132"', output)
        self.assertEqual(output.count('"192.168.70.129/26"'), 2)
        self.assertNotIn('192.168.71.', output)
        env = {'OAI_AMF_IP':'10.0.0.2', 'OAI_GNB_IP_CIDR':'10.0.0.1/24'}
        self.assertEqual(configure(template, env).count('"10.0.0.1/24"'), 2)
        with self.assertRaises(ValueError): configure('', {})
        with self.assertRaises(ValueError): addresses({'OAI_AMF_IP':'bad'})

    @patch('network_config.subprocess.run')
    @patch('network_config.subprocess.check_output')
    def test_binding_and_route(self, output, run):
        output.return_value = '[{"addr_info":[{"local":"192.168.70.129"}]}]'
        run.return_value = subprocess.CompletedProcess([], 0, '[{"dev":"bridge"}]')
        self.assertEqual(check_network({})['amf_ip'], '192.168.70.132')
        run.assert_called_once_with(['ip','-j','-4','route','get','192.168.70.132','from','192.168.70.129'], capture_output=True,text=True)
        run.return_value = subprocess.CompletedProcess([], 2, '')
        with self.assertRaisesRegex(ValueError, '路由'): check_network({})
        output.return_value = '[]'
        with self.assertRaisesRegex(ValueError, '不属于本机'): check_network({})

if __name__ == '__main__': unittest.main()