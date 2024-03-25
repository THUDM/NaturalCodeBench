import os
import re
import time
from collections import defaultdict
from pathlib import Path
import numpy as np
from tqdm import tqdm
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import load_jsonl, save_jsonl, load_json, save_json, estimate_pass_at_k
from exec_java import eval_test


def run_python_test(base_dir, test_dir):
    with open(Path(base_dir, test_dir, 'log.txt'), 'wb') as fp:
        subprocess.run(['python', 'ncb/exec_python.py', '--base_dir', base_dir, '--test_dir', test_dir],
                       stdout=fp, stderr=fp, timeout=840)


def execution(base_dir, ckpt, language, natural_lang, dataset_size, ks, num_workers=16, debug=False):
    start_time = time.time()
    work_dir = os.getcwd()
    base_dir = Path(work_dir, base_dir)
    test_dirs = os.listdir(base_dir)
    if 'error.jsonl' in test_dirs:
        test_dirs.remove('error.jsonl')
    if 'result.json' in test_dirs:
        test_dirs.remove('result.json')
    if 'raw_result.json' in test_dirs:
        test_dirs.remove('raw_result.json')
    if 'error_problems.jsonl' in test_dirs:
        test_dirs.remove('error_problems.jsonl')
    if language == 'python':
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(run_python_test, base_dir, _dir) for _dir in test_dirs]

            for future in tqdm(as_completed(futures), total=len(futures)):
                try:
                    result = future.result()
                except subprocess.TimeoutExpired as e:
                    print(e)

        os.chdir(work_dir)
        overall_result = {'total': 0, 'passed': 0, 'failed': 0}
        pass_statistics = {'0': 0, '0_30': 0, '30_60': 0, '60_100': 0, '100': 0}
        error = {'SyntaxError': 0, 'RuntimeError': 0}
        error_report = []
        error_problems = []
        results = defaultdict(list)
        for _dir in test_dirs:
            try:
                error_report.extend(load_jsonl(base_dir / _dir / 'error_report.jsonl'))
                error_cases = load_json(base_dir / _dir / 'error.json')
                for key in error.keys():
                    error[key] += error_cases[key]
                raw_result = load_json(base_dir / _dir / 'raw_result.json')
                for key in overall_result.keys():
                    overall_result[key] += raw_result['overall_result'][key]
                for key in pass_statistics.keys():
                    pass_statistics[key] += raw_result['pass_cases'][key]

                _id = str(_dir)[str(_dir).find('_')+1:str(_dir).rfind('_')]
                results[_id].append(raw_result['pass_cases'])

                if error_cases['RuntimeError'] > 0:
                    if debug:
                        print("RuntimeError: ", _dir)
                    error_problems.append({'problem': _dir, 'error': 'RuntimeError'})
                elif error_cases['SyntaxError'] > 0:
                    if debug:
                        print("SyntaxError: ", _dir)
                    error_problems.append({'problem': _dir, 'error': 'SyntaxError'})
                elif raw_result['pass_cases']['100'] <= 0:
                    if debug:
                        print("Not Pass All: ", _dir)
                    error_problems.append({'problem': _dir, 'error': 'Not Pass All'})
            except Exception as e:
                _id = str(_dir)[str(_dir).find('_') + 1:str(_dir).rfind('_')]
                results[_id].append({'0': 1, '0_30': 0, '30_60': 0, '60_100': 0, '100': 0})
                print(f"Error occur in {_dir}, error: {e}")

        total, correct = [], []
        for result in results.values():
            passed = [r['100'] for r in result]
            total.append(len(passed))
            correct.append(sum(passed))
        total, correct = np.array(total), np.array(correct)
        pass_at_k = {f"pass@{k}": round(estimate_pass_at_k(total, correct, k).mean() * 100, 1)
                     for k in ks if (total >= k).all()}
            
        end_time = time.time() - start_time
        print(f"Total Running time {end_time}")
        save_json({'overall_result': overall_result, 'pass_cases': pass_statistics, 'error_cases': error},
                  base_dir / 'raw_result.json')
        save_jsonl(error_problems, base_dir / 'error_problems.jsonl')
        save_jsonl(error_report, base_dir / 'error.jsonl')
        return {'result': {'pass@k': pass_at_k,
                           'time': end_time,
                           },
                'error': {'SyntaxError': round(error['SyntaxError'] / dataset_size * 100, 1),
                          'RuntimeError': round(error['RuntimeError'] / dataset_size * 100, 1)},
                'ckpt_name': ckpt,
                'benchmark': f'ncb_{language}_{natural_lang}'}
    elif language == 'java':
        JUnit_path = Path(os.getcwd(), 'JUnit')
        reports = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for _dir in test_dirs:
                if _dir == '.DS_Store' or _dir.endswith('.jsonl') or _dir == 'java' or _dir == 'java_test':
                    continue

                solution_dir = base_dir / 'java'
                test_dir = base_dir / 'java_test'
                os.makedirs(solution_dir, exist_ok=True)
                os.makedirs(test_dir, exist_ok=True)
                futures.append(executor.submit(eval_test, _dir, base_dir, JUnit_path, 420))

            for future in tqdm(as_completed(futures), total=len(futures)):
                reports.append(future.result())

        found_pattern = f"Found (.*?) tests"
        failed_pattern = f"Failed (.*?) tests"
        pr_pattern = f"Passed rate: (.*?)\n"
        total_c = 0
        suc = 0
        pr_0 = 0
        pr_0_3 = 0
        pr_3_6 = 0
        pr_6_10 = 0
        pr_1 = 0
        cp_error = 0
        exe_error = 0
        results = defaultdict(list)
        error_problems = []
        for i in reports:
            _id = i['_id']
            if 'failed' not in i['test_result'] and 'Found' in i['test_result']:
                total_c += int(re.search(found_pattern, i['test_result'], re.DOTALL).group(1))
                suc += int(re.search(found_pattern, i['test_result'], re.DOTALL).group(1)) - int(
                    re.search(failed_pattern, i['test_result'], re.DOTALL).group(1))
                ma = re.search(pr_pattern, i['test_result'], re.DOTALL)
                pr = float(ma.group(1))
                if pr == 0:
                    pr_0 += 1
                elif pr > 0 and pr < 0.3:
                    pr_0_3 += 1
                elif pr >= 0.3 and pr < 0.6:
                    pr_3_6 += 1
                elif pr >= 0.6 and pr < 1:
                    pr_6_10 += 1
                elif pr == 1:
                    pr_1 += 1
                results[_id].append(pr == 1)

                if pr != 1:
                    if debug:
                        print("Not Pass All:", i['class_name'])
                    error_problems.append({'problem': i['class_name'], 'error': 'Not Pass All'})
            else:
                if i['compile_error'] == "" and i['exe_error'] != "":
                    if debug:
                        print("EXEC_error:", i['class_name'])
                    exe_error += 1
                    error_problems.append({'problem': i['class_name'], 'error': 'EXEC_error'})
                else:
                    if debug:
                        print("CP_error:", i['class_name'])
                    cp_error += 1
                    error_problems.append({'problem': i['class_name'], 'error': 'CP_error'})

                results[_id].append(False)

        total, correct = [], []
        for result in results.values():
            passed = [int(r) for r in result]
            total.append(len(passed))
            correct.append(sum(passed))
        total, correct = np.array(total), np.array(correct)
        pass_at_k = {f"pass@{k}": round(estimate_pass_at_k(total, correct, k).mean() * 100, 1)
                     for k in ks if (total >= k).all()}

        raw_result = {'overall_result': {
                        'total': total_c,
                        'passed': suc,
                    },
                   'pass_cases': {
                        '0': pr_0,
                        '0_30': pr_0_3,
                        '30_60': pr_3_6,
                        '60_100': pr_6_10,
                        '100': pr_1
                   }}
        save_json(raw_result, base_dir / 'raw_result.json')
        save_jsonl(error_problems, base_dir / 'error_problems.jsonl')
        end_time = time.time() - start_time
        print(f"Total Running time {end_time}")
        return {'result': {'pass@k': pass_at_k,
                           'time': end_time},
                'error': {'CompileError': round(cp_error / dataset_size * 100, 1),
                          'ExecutionError': round(exe_error / dataset_size * 100, 1)},
                'ckpt_name': ckpt,
                'benchmark': f'ncb_{language}_{natural_lang}'}
