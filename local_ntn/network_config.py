"""本地实验的 N2/N3 地址；与外部 OAI 模板解耦。"""
import ipaddress
import json
import os
import re
import subprocess


def addresses(environment=None):
    env = os.environ if environment is None else environment
    amf = ipaddress.IPv4Address(env.get('OAI_AMF_IP', '192.168.70.132'))
    gnb = ipaddress.IPv4Interface(env.get('OAI_GNB_IP_CIDR', '192.168.70.129/26'))
    if amf.is_unspecified or amf.is_multicast or gnb.ip.is_unspecified or gnb.ip.is_multicast:
        raise ValueError('AMF/gNB 必须使用有效单播 IPv4 地址')
    return str(amf), str(gnb)


def configure(text, environment=None):
    amf, gnb = addresses(environment)
    # 仅修改新生成的配置；计数检查避免模板变化被静默忽略。
    patterns = [
        (r'(\bamf_ip_address\s*=\s*\(\s*\{\s*ipv4\s*=\s*)"[^"]+"', amf),
        (r'(\bGNB_IPV4_ADDRESS_FOR_NG_AMF\s*=\s*)"[^"]+"', gnb),
        (r'(\bGNB_IPV4_ADDRESS_FOR_NGU\s*=\s*)"[^"]+"', gnb),
    ]
    for pattern, value in patterns:
        text, count = re.subn(pattern, lambda match: match[1] + '"' + value + '"', text)
        if count != 1:
            raise ValueError('核心网地址字段必须恰好出现一次，实际为 ' + str(count))
    return text


def check_network(environment=None):
    """启动前只读检查；核心网网桥必须已经启动，不创建或改写地址。"""
    amf, cidr = addresses(environment)
    source = str(ipaddress.IPv4Interface(cidr).ip)
    interfaces = json.loads(subprocess.check_output(['ip', '-j', '-4', 'addr', 'show'], text=True))
    assigned = {item['local'] for interface in interfaces for item in interface.get('addr_info', [])}
    if source not in assigned:
        raise ValueError(f'gNB 绑定地址 {source} 不属于本机；请先启动本地核心网，或检查 OAI_GNB_IP_CIDR')
    result = subprocess.run(['ip', '-j', '-4', 'route', 'get', amf, 'from', source], capture_output=True, text=True)
    if result.returncode or not json.loads(result.stdout):
        raise ValueError(f'gNB 地址 {source} 没有到 AMF {amf} 的可用路由')
    return {'amf_ip': amf, 'gnb_ip_cidr': cidr}