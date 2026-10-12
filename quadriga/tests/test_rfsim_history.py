"""编译实际 RFsim 队列清理代码，检查长多径历史和启动边界。"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class HistoryRetentionTest(unittest.TestCase):
    def test_actual_queue_cleanup(self):
        repo = Path(os.environ['OAI_REPO'])
        source = (repo / 'radio/rfsimulator/simulator.cpp').read_text()
        end = source.index('clear_old_packets(ptr->received_packets, timestamp_to_free);')
        # 从清理分支首个声明开始提取，使用生产语句而非复制算法。
        branch = source.rfind('if (ptr->conn_sock != -1 && !ptr->received_packets.empty()) {', 0, end)
        body = source[source.index('{', branch) + 1:end]
        program = r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstddef>
#include <cstdio>
using openair0_timestamp_t = int64_t;
struct Channel { uint64_t channel_length, channel_offset; };
struct Buffer { Channel *channel_model; };
struct State { openair0_timestamp_t nextRxTstamp; uint64_t chan_offset; };
static size_t qd_channel_history_length(Channel *) { return 33886; }
static uint64_t cutoff(State *t, Buffer *ptr) {
''' + body + r'''
  return timestamp_to_free;
}
int main() {
  Channel ch{1, 200000}; Buffer ptr{&ch}; State t{1000000, 200000};
  const uint64_t expected = 1000000 - 1 - 200000 - (33886 - 1);
  std::printf("cleanup cutoff=%lu expected=%lu\n", cutoff(&t, &ptr), expected);
  assert(cutoff(&t, &ptr) == expected);
  t.nextRxTstamp = 100; assert(cutoff(&t, &ptr) == 0);
  t.nextRxTstamp = 0; assert(cutoff(&t, &ptr) == 0);
  t.nextRxTstamp = -1; assert(cutoff(&t, &ptr) == 0);
  ptr.channel_model = nullptr;
  t.nextRxTstamp = 100; assert(cutoff(&t, &ptr) == 0);
  t.nextRxTstamp = 1000000; assert(cutoff(&t, &ptr) == 799999);
  puts("PASS actual RFsim cleanup: long history and startup saturation");
}
'''
        with tempfile.TemporaryDirectory(prefix='qd-history-') as directory:
            path = Path(directory)
            (path / 'test.cpp').write_text(program)
            subprocess.run(['c++', '-std=c++17', '-Wall', '-Wextra',
                            str(path / 'test.cpp'), '-o', str(path / 'test')], check=True)
            subprocess.run([str(path / 'test')], check=True)


    def test_actual_input_collection(self):
        repo = Path(os.environ['OAI_REPO'])
        source = (repo / 'radio/rfsimulator/simulator.cpp').read_text()
        begin = source.index('static void combine_received_beams(')
        end = source.index('static bool flushInput', begin)
        combine = source[begin:end]
        begin = source.index('const uint64_t channel_offset = ptr->channel_model->channel_offset;')
        end = source.index('      } else {', begin)
        collection = source[begin:end]
        program = r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <cmath>
#include <queue>
#include <vector>
using uint = unsigned int;
using openair0_timestamp_t = int64_t;
struct c16_t { int16_t r, i; };
using cf_t = c16_t;
struct Header { uint64_t timestamp, size, beam_map; };
struct rfsim_packet_t { Header header; void *payload; };
struct Channel { uint64_t channel_offset; size_t history; };
struct Buffer { Channel *channel_model; uint nbAnt; std::queue<rfsim_packet_t *> received_packets; };
struct rfsimulator_state_t {};
#define AssertFatal(cond, ...) assert(cond)
static size_t qd_channel_history_length(Channel *c) { return c->history; }
static float get_rx_gain_db(rfsimulator_state_t *, int, int) { return 0; }
static std::vector<int> beam_map_to_beams(uint64_t) { return {0}; }
static void rxAddInput(c16_t **input, cf_t *out, int, Channel *ch, int n) {
  memcpy(out,input[0]+ch->history-1,n*sizeof(*out));
}
''' + combine + r'''
static void collect(rfsimulator_state_t *t, Buffer *ptr, openair0_timestamp_t timestamp,
                    int nsamps, cf_t **temp_array) {
  int nbAnt=1,rx_beam_id=0;
''' + collection + r'''
}
int main() {
  rfsimulator_state_t state;Channel ch{0,4};Buffer b{&ch,1,{}};
  c16_t payload[128];for(int i=0;i<128;i++)payload[i]={int16_t(i+1),int16_t(-i-1)};
  rfsim_packet_t packet{{0,128,1},payload};b.received_packets.push(&packet);
  cf_t out[16],*outputs[]={out};
  auto check=[&](int64_t ts,uint64_t offset,size_t history) {
    ch.channel_offset=offset;ch.history=history;memset(out,0,sizeof(out));
    collect(&state,&b,ts,16,outputs);
    for(int i=0;i<16;i++) {
      const int64_t wanted=ts-int64_t(offset)+i;
      const int expected=wanted>=0 && wanted<128 ? wanted+1 : 0;
      assert(out[i].r==expected);assert(out[i].i==-expected);
    }
  };
  check(2,0,4);check(2,4,4);check(8,0,4);check(8,6,4);check(8,1,4);
  check(0,200000,33886);check(200010,200000,33886);
  check(128,0,4);check(140,0,4);
  assert(b.received_packets.size()==1);
  puts("PASS actual RFsim collection: startup padding, changing bulk offset, long history, tail");
}
'''
        with tempfile.TemporaryDirectory(prefix='qd-collection-') as directory:
            path = Path(directory)
            (path / 'test.cpp').write_text(program)
            subprocess.run(['c++', '-std=c++17', '-Wall', '-Wextra',
                            '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                            str(path / 'test.cpp'), '-o', str(path / 'test')], check=True)
            subprocess.run([str(path / 'test')], check=True)


if __name__ == '__main__':
    unittest.main()
