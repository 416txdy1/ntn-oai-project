// 本地覆盖：仅从控制面规则选择下行 QFI，不依赖首个上行包。
#pragma once
#include <cstdint>

namespace ntn_upf {
// 模板允许独立测试选择策略；生产调用使用真实 PFCP session/PDR 类型。
template <class Session, class Pdr>
bool downlink_qfi(const Session& session, const Pdr& downlink,
                  uint8_t& result) {
  if (downlink.qer_id.first) {
    for (const auto& qer : session.qers) {
      if (qer && qer->qer_id.first &&
          qer->qer_id.second.qer_id == downlink.qer_id.second.qer_id) {
        if (!qer->qfi.first || qer->qfi.second.qfi == 0 ||
            qer->qfi.second.qfi > 63) return false;
        result = qer->qfi.second.qfi;
        return true;
      }
    }
    return false;  // 显式关联缺失时不能回退到其他流。
  }
  // v2.2.1 SMF 的无 QER 单流模式：ACCESS=0，仅接受唯一有效的规则 QFI。
  uint8_t selected = 0;
  for (const auto& pdr : session.pdrs) {
    if (!pdr || !pdr->pdi.first || !pdr->pdi.second.source_interface.first)
      continue;
    const auto& pdi = pdr->pdi.second;
    if (pdi.source_interface.second.interface_value != 0) continue;
    if (!pdi.qfi.first || pdi.qfi.second.qfi == 0 || pdi.qfi.second.qfi > 63)
      return false;
    const uint8_t candidate = pdi.qfi.second.qfi;
    if (selected != 0 && selected != candidate) return false;
    selected = candidate;
  }
  if (selected == 0) return false;
  result = selected;
  return true;
}
}  // namespace ntn_upf
