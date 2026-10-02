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


if __name__ == '__main__':
    unittest.main()
