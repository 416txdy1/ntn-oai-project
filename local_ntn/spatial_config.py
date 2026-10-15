"""独立生成多端口配置；不覆盖 OAI 原始模板或私有 UE 配置。"""
from __future__ import annotations
import re
from collections.abc import Mapping


def spatial_mode(environment: Mapping[str, str]) -> bool:
    mode = environment.get("OAI_SPATIAL_MODE", "siso")
    if mode not in {"siso", "miso2", "miso4", "miso4-subarray"}:
        raise ValueError("OAI_SPATIAL_MODE 只支持 siso、miso2、miso4 或 miso4-subarray")
    return mode != "siso"


def spatial_ports(environment: Mapping[str, str]) -> int:
    """卫星端独立 RF 端口数量；先验证模式，禁止静默回退。"""
    return int(environment["OAI_SPATIAL_MODE"][4]) if spatial_mode(environment) else 1


def configure_miso(config: str, ports: int = 2) -> str:
    """原生 OAI 2/4 个发射接收通道，UE 单天线，最多一层 PDSCH。"""
    if ports not in (2, 4):
        raise ValueError("空间配置仅支持 2 或 4 个端口")
    for name in ("nb_tx", "nb_rx"):
        config, count = re.subn(r"(?m)^(\s*" + name + r"\s*=)[^;]+;", rf"\g<1> {ports};", config)
        if count != 1:
            raise ValueError(f"{name}: 需要唯一 RU 端口配置")
    settings = {"pdsch_AntennaPorts_N1": ports // 2, "pdsch_AntennaPorts_N2": 1,
                "pdsch_AntennaPorts_XP": 2, "maxMIMO_layers": 1, "do_CSIRS": 1}
    # 字段属于 gNB 实例；只改生成副本，保留原模板。
    insertion = ""
    for name, value in settings.items():
        pattern = r"(?m)^(\s*" + name + r"\s*=)[^;]+;"
        config, count = re.subn(pattern, rf"\g<1> {value};", config)
        if count > 1:
            raise ValueError(f"{name}: 重复配置")
        if not count:
            insertion += f"    {name} = {value};\n"
    config, count = re.subn(r"(gNBs\s*=\s*\(\s*\{)", lambda m: m[1] + ("\n" + insertion if insertion else ""), config, count=1)
    if count != 1:
        raise ValueError("缺少 gNBs 实例")
    return config
