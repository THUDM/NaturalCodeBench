import argparse
import os
import sys
sys.path.append(os.getcwd())
from pathlib import Path
import pytest
from pytest_jsonreport.plugin import JSONReport
from utils import save_jsonl, save_json


def level(rate):
    if rate == 0:
        return '0'
    elif 0 < rate < 30:
        return '0_30'
    elif 30 <= rate < 60:
        return '30_60'
    elif 60 <= rate < 100:
        return '60_100'
    elif rate == 100:
        return '100'


def run_python_test(base_dir, test_dir):
    _id = test_dir[test_dir.rfind('_')+1:]
    os.chdir(Path(base_dir, test_dir))

    overall_result = {'total': 0, 'passed': 0, 'failed': 0}
    pass_statistics = {'0': 0, '0_30': 0, '30_60': 0, '60_100': 0, '100': 0}
    error = {'SyntaxError': 0, 'RuntimeError': 0}
    error_report = []
    error_cases = 0

    plugin = JSONReport()
    pytest.main(['-s', '--cov', '--cov-report', 'json', '--disable-warnings'], plugins=[plugin])

    if len(plugin.report.get('tests')) == 0:
        longrepr = plugin.report['collectors'][1]['longrepr']
        error_report.append({"_id": _id, 'nodeid': plugin.report['collectors'][1]['nodeid'], 'longrepr': longrepr})
        if "SyntaxError" in longrepr:
            error['SyntaxError'] += 1
        else:
            error['RuntimeError'] += 1
        save_json(error, Path(base_dir, test_dir, 'error.json'))
        save_jsonl(error_report, Path(base_dir, test_dir, 'error_report.jsonl'))
        save_json({'overall_result': overall_result, 'pass_cases': pass_statistics},
                  Path(base_dir, test_dir, 'raw_result.json'))
        return
    try:
        error_report.append({"_id": _id, "testcases_traceback": []})
        for case in plugin.report.get('tests'):
            print(case)
            if 'traceback' not in case['call']:
                continue
            if 'AssertionError' not in case['call']['traceback'][0]['message']:
                error_cases += 1
                error_report[0]['testcases_traceback'].append({'nodeid': case['nodeid'],
                                                              'traceback': case['call']['longrepr']})
    except Exception as e:
        pass
    error['RuntimeError'] += 1 if error_cases != 0 else 0

    summary = plugin.report.get("summary")
    passed = summary.get("passed", 0)
    total = summary.get("total", 0)
    overall_result['passed'] += passed
    overall_result['total'] += total
    if total != 0:
        pass_rate = (passed / total) * 100
        pass_statistics[level(pass_rate)] += 1
    
    if len(error_report[0]['testcases_traceback']) == 0:
        error_report = []
    save_jsonl(error_report, Path(base_dir, test_dir, 'error_report.jsonl'))
    save_json(error, Path(base_dir, test_dir, 'error.json'))
    save_json({'overall_result': overall_result, 'pass_cases': pass_statistics},
              Path(base_dir, test_dir, 'raw_result.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, required=True)
    parser.add_argument('--test_dir', type=str, required=True)
    args = parser.parse_args()

    run_python_test(args.base_dir, args.test_dir)
