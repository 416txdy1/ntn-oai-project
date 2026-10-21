# 启动器检查记录（2026-10-19）

本次新增独立 Windows 入口及编排/显示工具，没有修改已验收的仿真运行源码。

- PowerShell `System.Management.Automation.Language.Parser::ParseFile`：语法错误0。
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ntn_test_launcher\launch.ps1 -CheckOnly`：exit0。
  实际经过Windows→WSL→sudo→Python，找到Ubuntu-22.04中的独立平台。
  初次检查发现Windows反斜杠路径被WSL解释的问题，已改为正斜杠和`--exec`，再次检查通过。
- 在WSL执行 `python3 -B <Windows目录的WSL路径>/ntn_test_launcher/test_launcher.py`：8 tests，OK，exit0。
  覆盖部分写入、缺失文件、敏感行过滤、切换阶段去重、在途/最终丢包语义区分、
  子进程失败退出码、验收失败后modem/core清理顺序、清理失败仍继续core清理、
  真实Linux子进程超时中断及固定五轮顺序/参数（部分项目合并在同一测试中）。
- 首次尝试在Windows沙箱运行测试时遇到系统临时目录权限错误，未视为通过；最终测试在目标WSL中完成。
- `git diff --check`：exit0（对现有跟踪文件的检查；新增文件仍为未提交文件）。

没有运行本入口的完整构建、OAI trace/IQ回归或真实五轮业务仿真，
因此上述结果只证明启动链路与离线编排测试通过，不是新一轮仿真验收证据。
完整实验由用户双击入口后执行，结论以该次suite-report.json与各场景report.json为准。
