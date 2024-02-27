import subprocess
import copy
import os
from pathlib import Path
from utils import save_json


def excute(tmp_dir: str, JUnit_path: str, timeout: int):
    if not tmp_dir:
        raise ValueError(f"pls enter the path for executing java")
    JUnit = f':{JUnit_path}/*'
    tr_file = "TestRunner.java"
    tr_name = "TestRunner"
    compilation_result = subprocess.run(["javac", "-cp",JUnit,tr_file], cwd=tmp_dir, timeout=timeout,capture_output=True)
    compile_returncode = compilation_result.returncode
    if compile_returncode == 0:
        try:
            exec_result = subprocess.run(["java", "-cp",JUnit,tr_name], cwd=tmp_dir, timeout=timeout,capture_output=True)
            if exec_result.returncode == 0:
                res = exec_result.stdout.decode()
            elif exec_result.returncode == 1:
                res = f"failed: execute error:\n{exec_result.stderr.decode()}"
        except subprocess.TimeoutExpired as e:
            res = "time out"
        except BaseException as e:
            res = f"failed: {e}"
    else:
        compile_error = compilation_result.stderr.decode('utf-8')
        res = f'failed: compilation error:\n{compile_error}'
    return res


def eval_test(class_name, base_dir, JUnit_path, timeout: int):
    item = {}
    _id = class_name[class_name.find('_')+1:class_name.rfind('_')]
    base_dir = copy.deepcopy(base_dir)
    tmp_dir = Path(base_dir, class_name)
    compile_error = ""
    exe_error = ""
    _id = _id = str(class_name)[str(class_name).find('_')+1:str(class_name).rfind('_')]
    if not os.listdir(tmp_dir):
        item['_id'] = _id
        item['class_name'] = class_name
        item["compile_error"] = compile_error
        item["exe_error"] = exe_error
        item["test_result"] = 'nocode'
        save_json(item, Path(base_dir, tmp_dir, 'eval_report.json'))
        return item
    res = excute(tmp_dir, JUnit_path, timeout=timeout)
    if 'failed: compilation error' in res:
        compile_error = res

    if 'failed: execute error:' in res:
        exe_error = res

    item['_id'] = _id
    item['class_name'] = class_name
    item["compile_error"] = compile_error
    item["exe_error"] = exe_error
    item["test_result"] = res

    save_json(item, Path(base_dir, tmp_dir, 'eval_report.json'))
    return item
