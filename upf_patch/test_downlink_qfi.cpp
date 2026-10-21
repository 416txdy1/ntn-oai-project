#include "downlink_qfi.hpp"
#include <cassert>
#include <memory>
#include <vector>
#include <utility>
#include <iostream>
// 仅保留选择器读取的字段；真实 PFCP 类型另由完整 UPF 构建检查。
struct Qfi { unsigned qfi = 0; };
struct QerId { unsigned qer_id = 0; };
struct Interface { unsigned interface_value = 0; };
struct Pdi {
  std::pair<bool, Interface> source_interface;
  std::pair<bool, Qfi> qfi;
};
struct Pdr { std::pair<bool, QerId> qer_id; std::pair<bool, Pdi> pdi; };
struct Qer { std::pair<bool, QerId> qer_id; std::pair<bool, Qfi> qfi; };
struct Session { std::vector<std::shared_ptr<Pdr>> pdrs; std::vector<std::shared_ptr<Qer>> qers; };
std::shared_ptr<Pdr> uplink(unsigned qfi) {
  auto p=std::make_shared<Pdr>();
  p->pdi={true,{{true,{0}},{true,{qfi}}}};
  return p;
}
int main() {
  Session s; Pdr dl; uint8_t out=99; unsigned checks=0;
  auto expect=[&](bool ok,unsigned value=99) {
    out=99;
    assert(ntn_upf::downlink_qfi(s,dl,out)==ok);
    assert(out==value); ++checks;
  };
  expect(false);                         // 无规则不能硬编码 QFI=5。
  s.pdrs={uplink(1)}; expect(true,1);     // 没有任何上行包也能正确选首包。
  s.pdrs={uplink(9)}; expect(true,9);     // 不是硬编码 QFI=1。
  s.pdrs.push_back(uplink(9)); expect(true,9);
  s.pdrs.push_back(uplink(1)); expect(false); // 多流歧义禁止任意选择。
  s.pdrs={uplink(0)}; expect(false);
  s.pdrs={uplink(64)}; expect(false);
  s.pdrs={uplink(63)}; expect(true,63);
  s.pdrs[0]->pdi.second.qfi.first=false; expect(false);
  s.pdrs={uplink(1)};
  auto unrelated=uplink(8); unrelated->pdi.second.source_interface.second.interface_value=1;
  s.pdrs.push_back(unrelated); expect(true,1); // 下行 PDI 不是上行流候选。
  dl.qer_id={true,{17}}; expect(false); // 显式 QER 缺失不能降级到单流回退。
  auto q=std::make_shared<Qer>(); q->qer_id={true,{17}}; q->qfi={true,{7}};
  s.qers={q}; expect(true,7);          // 匹配 QER 优先于其他上行流。
  auto other=std::make_shared<Qer>();other->qer_id={true,{18}};other->qfi={true,{4}};
  s.qers.insert(s.qers.begin(),other); expect(true,7);
  q->qfi.first=false; expect(false);
  q->qfi={true,{0}}; expect(false);
  q->qfi={true,{64}}; expect(false);
  q->qfi={true,{63}}; expect(true,63);
  q->qer_id.first=false; expect(false);
  std::cout << checks << " QFI selection cases passed\n";
}
