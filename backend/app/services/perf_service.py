import subprocess
import json
import os
from datetime import datetime

class PerfService:
    @staticmethod
    def run_perf_test(test_case, parameters):
        result = {
            'start_time': datetime.utcnow(),
            'status': 'running',
            'perf_data': None,
            'benchmark_data': None,
            'flamegraph_path': None
        }
        
        try:
            # 执行perf命令
            cmd = f"perf record -g {test_case.command}"
            subprocess.run(cmd, shell=True, check=True)
            
            # 生成perf报告
            perf_output = subprocess.check_output("perf report --stdio", shell=True)
            result['perf_data'] = perf_output.decode()
            
            # 生成火焰图
            subprocess.run("perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg", shell=True)
            result['flamegraph_path'] = "flamegraph.svg"
            
            result['status'] = 'completed'
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            
        result['end_time'] = datetime.utcnow()
        return result