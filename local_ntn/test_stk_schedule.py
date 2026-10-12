import csv
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


def test_schedule_parser_and_previous_row_lookup():
    if shutil.which("cc") is None:
        pytest.skip("C compiler is available in the WSL/OAI build environment")
    root = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        schedule = td / "schedule.csv"
        with schedule.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["time", "satellite_id", "elevation_deg", "visible", "switched"])
            w.writerow([10, "SAT_A", 20, 1, 1])
            w.writerow([20, "SAT_B", 15, 1, 1])
        source = td / "test.c"
        source.write_text(
            '#include "stk_schedule.h"\n'
            '#include <stdio.h>\n'
            'int main(int argc,char **argv){(void)argc;stk_schedule s={0};char e[128];'
            'if(!stk_schedule_load(argv[1],&s,e,sizeof(e)))return 1;'
            'stk_schedule_entry x={0};if(!stk_schedule_at(&s,19,&x))return 2;'
            'printf("%s %.0f\\n",x.satellite_id,x.elevation_deg);'
            'stk_schedule_free(&s);return 0;}\n', encoding="utf-8"
        )
        exe = td / "test"
        subprocess.run(["cc", "-Wall", "-Wextra", "-Werror", "-I", str(root),
                        str(source), str(root / "stk_schedule.c"), "-o", str(exe)], check=True)
        result = subprocess.run([str(exe), str(schedule)], check=True, capture_output=True, text=True)
        assert result.stdout.strip() == "SAT_A 20"


def test_schedule_parser_reads_handover_phase_metadata():
    if shutil.which("cc") is None:
        pytest.skip("C compiler is available in the WSL/OAI build environment")
    root = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        schedule = td / "handover.csv"
        schedule.write_text(
            "time,satellite_id,elevation_deg,visible,switched,handover_phase,"
            "previous_satellite_id,next_satellite_id\n"
            "20,SAT_B,15,1,1,complete,SAT_A,SAT_B\n", encoding="utf-8"
        )
        source = td / "test.c"
        source.write_text(
            '#include "stk_schedule.h"\n'
            '#include <stdio.h>\n'
            'int main(int argc,char **argv){(void)argc;stk_schedule s={0};char e[128];'
            'if(!stk_schedule_load(argv[1],&s,e,sizeof(e)))return 1;'
            'stk_schedule_entry x={0};if(!stk_schedule_at(&s,20,&x))return 2;'
            'printf("%s %s %s\\n",x.handover_phase,x.previous_satellite_id,x.next_satellite_id);'
            'stk_schedule_free(&s);return 0;}\n', encoding="utf-8"
        )
        exe = td / "test"
        subprocess.run(["cc", "-Wall", "-Wextra", "-Werror", "-I", str(root),
                        str(source), str(root / "stk_schedule.c"), "-o", str(exe)], check=True)
        result = subprocess.run([str(exe), str(schedule)], check=True, capture_output=True, text=True)
        assert result.stdout.strip() == "complete SAT_A SAT_B"
