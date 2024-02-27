import os
import re
import shutil
from pathlib import Path
from tqdm import tqdm
from utils import save_json


def extract_python_code(response):
    tag_pattern = fr"\[Python\](.*?)\[/Python\]"
    tag_pattern1 = fr"\[Python\](.*?)```"
    tag_pattern2 = fr"\[Python\](.*?)"
    py_pattern1 = fr"```python[\n\r](.*?)[\n\r]```"
    py_pattern2 = fr"```[\n\r](.*?)[\n\r]```"
    py_pattern3 = fr"def\s(.*)"
    py_pattern4 = fr"class\s(.*)"
    py_pattern5 = fr"import\s(.*)"
    py_pattern6 = fr"from\s(.*)"

    try:
        judge = re.search(tag_pattern, response, re.DOTALL)
        if judge and '```' not in judge.group(1):
            code = judge.group(1)
        elif not judge and '[Python]' in response and '```python' not in response:
            if '```' in response[response.find('[Python]'):]:
                code = re.search(tag_pattern1, response, re.DOTALL).group(1)
            else:
                code = re.search(tag_pattern2, response, re.DOTALL).group(1)
        elif '```python' in response:
            code = re.search(py_pattern1, response, re.DOTALL).group(1)
        elif '```' in response:
            code = re.search(py_pattern2, response, re.DOTALL).group(1)
        elif 'from ' in response and 'import ' in response:
            if response.find('from') < response.find('import'):
                code = re.search(py_pattern6, response, re.DOTALL).group()
            else:
                code = re.search(py_pattern5, response, re.DOTALL).group()
        elif 'import ' in response:
            code = re.search(py_pattern5, response, re.DOTALL).group()
        elif 'from ' in response:
            code = re.search(py_pattern6, response, re.DOTALL).group()
        elif 'class ' in response:
            code = re.search(py_pattern4, response, re.DOTALL).group()
        elif 'def ' in response:
            code = re.search(py_pattern3, response, re.DOTALL).group()
        else:
            code = 'NaN'
    except Exception as e:
        code = 'NaN'
    code = 'import pytest\n' + code
    return code


def extract_java_code(response):
    tag_pattern = fr"\[Java\](.*?)\[/Java\]"
    java_pattern1 = fr"```java[\n\r](.*?)[\n\r]```"
    java_pattern2 = fr"public\s(.*)}}"
    java_pattern3 = fr"```Java(.*?)```"
    java_pattern4 = fr"```[\n\r](.*?)[\n\r]```"
    java_pattern5 = fr"import\s(.*)}}"
    java_pattern6 = fr"class\s(.*)}}"
    java_pattern7 = fr"interface\s(.*)}}"

    try:
        if '[Java]' in response:
            code = [re.search(tag_pattern, response, re.DOTALL).group(1)]
        elif '```java' in response or '```Java' in response or '```' in response:
            code = re.findall(java_pattern1, response, re.DOTALL)
            for c in code:
                response = response.replace("```java"+c+"```", "")
            code += re.findall(java_pattern3, response, re.DOTALL)
            for c in code:
                response = response.replace("```Java"+c+"```", "")
            code += re.findall(java_pattern4, response, re.DOTALL)
        elif 'import ' in response:
            code = [re.search(java_pattern5, response, re.DOTALL).group()]
        elif 'public ' in response or 'interface ' in response or 'class ' in response:
            public_ind = response.find('public ')
            interface_ind = response.find('interface ')
            class_ind = response.find('class ')
            if public_ind != -1 and \
                    (public_ind < interface_ind or interface_ind == -1) and \
                    (public_ind < class_ind or class_ind == -1):
                code = [re.search(java_pattern2, response, re.DOTALL).group()]
            elif interface_ind != -1 and \
                    (interface_ind < public_ind or public_ind == -1) and \
                    (interface_ind < class_ind or class_ind == -1):
                code = [re.search(java_pattern7, response, re.DOTALL).group()]
            elif class_ind != -1 and \
                    (class_ind < public_ind or public_ind) and \
                    (class_ind < interface_ind or interface_ind == -1):
                code = [re.search(java_pattern6, response, re.DOTALL).group()]
            else:
                code = "NaN"
                print(response)
        else:
            code = ['NaN']
    except Exception as e:
        code = ['NaN']
    return code


def extract_codes(data, testcases, language):
    for item in data:
        for ex in testcases:
            if item['_id'] == ex['_id']:
                item['testcases'] = ex['testcases']
                item['setup_code'] = ex['setup_code']
                break

        if 'code' not in item.keys():
            if language == 'java':
                item['code'] = extract_java_code(item['response'])
            elif language == 'python':
                item['code'] = extract_python_code(item['response'])
    return data


def write_python_test_files(data, data_dir, input_files_path, ckpt):
    ids = {}
    for item in data:
        _id = str(item['_id'])
        if not item['response'] or item['code'] == 'NaN':
            print(f"No extracted code: python_{item['_id']}")
            continue
        file_name = f'python_{_id}'
        if _id in ids:
            ids[_id] += 1
            id_name = _id + '_' + str(ids[_id])
        else:
            ids[_id] = 0
            id_name = _id + '_' + str(ids[_id])
        

        test_dir = data_dir / ckpt / f'python_{id_name}'
        os.makedirs(test_dir, exist_ok=True)

        save_json(item, test_dir / f'{file_name}.json')

        with open(test_dir / f'{file_name}.py', 'w', encoding='utf-8') as f:
            f.write("import pytest\nimport sys\nwith open('stdin.txt', 'w') as f:\n    for i in range(1000):\n        f.write(\"1\\n\")\nsys.stdin = open(\"stdin.txt\")\n")
            f.write(item['code'] + '\n')

        files_for_prob_dir = input_files_path / str(_id)
        if os.path.exists(files_for_prob_dir):
            for file in os.listdir(files_for_prob_dir):
                file_for_prob = files_for_prob_dir / str(file)
                if os.path.isfile(file_for_prob):
                    shutil.copy(file_for_prob, test_dir / str(file))
                elif os.path.isdir(file_for_prob):
                    shutil.copytree(file_for_prob, test_dir / str(file))

        with open(test_dir / f'test_{file_name}.py', 'w', encoding='utf-8') as f:
            f.write(f"import pytest\nfrom {file_name} import *\n")
            f.write(item['testcases'] + '\n' + item['setup_code'])


def write_java_test_files(data, data_dir, input_files_path, ckpt):
    Testrunner = """import org.junit.platform.launcher.Launcher;
    import org.junit.platform.launcher.LauncherDiscoveryRequest;
    import org.junit.platform.launcher.TestPlan;
    import org.junit.platform.launcher.TestExecutionListener;
    import org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder;
    import org.junit.platform.launcher.core.LauncherFactory;
    import org.junit.platform.launcher.listeners.SummaryGeneratingListener;
    import org.junit.platform.launcher.listeners.TestExecutionSummary;

    import static org.junit.platform.engine.discovery.DiscoverySelectors.selectClass;

    public class TestRunner {
        public static void main(String[] args) {
            LauncherDiscoveryRequest request = LauncherDiscoveryRequestBuilder.request()
                    .selectors(selectClass(YourTestClass.class))   // 替换为你的测试类
                    .build();

            Launcher launcher = LauncherFactory.create();

            // 创建和 注册 SummaryGeneratingListener
            SummaryGeneratingListener listener = new SummaryGeneratingListener();
            launcher.registerTestExecutionListeners(listener);

            // 执行测试
            launcher.execute(request);

            // 获得测试的结果汇总信息
            TestExecutionSummary summary = listener.getSummary();
            long testsFoundCount = summary.getTestsFoundCount();
            long testsFailedCount = summary.getTestsFailedCount();
            long testsSucceedCount = summary.getTestsSucceededCount();
            System.out.println("Found " + testsFoundCount + " tests");
            System.out.println("Failed " + testsFailedCount + " tests");
            System.out.println("Passed rate: " + (double)testsSucceedCount/testsFoundCount);
        }
    }"""
    ids = {}
    for index, item in tqdm(enumerate(data)):
        _id = str(item['_id'])
        if not item['response'] or item['code'] == 'NaN':
            print(f"no code: java_{item['_id']}")
            continue
        if _id in ids:
            ids[_id] += 1
            id_name = _id + '_' + str(ids[_id])
        else:
            ids[_id] = 0
            id_name = _id + '_' + str(ids[_id])
        test_dir = data_dir / ckpt / f"java_{id_name}"
        os.makedirs(test_dir, exist_ok=True)

        save_json(item, test_dir / f'java_{_id}.json')

        file_c = 0
        for c in item['code']:
            c = '\n' + c
            import_pattern = r'(\n|^)(import .*?)\n'
            interface_pattern = r"((@.*?)?(\n[^\n]*)?interface .*?[;}]\s*\n+})"
            class_pattern = r"((@.*?)?(\n[^\n]*)?class .*?[;}]\s*\n+})"
            enum_pattern = r"((@.*?)?(\n[^\n]*)?enum .*?[;}]?\s*\n+})"

            imports = re.findall(import_pattern, c, re.MULTILINE)
            imports = [i[1] for i in imports]
            interfaces = re.findall(interface_pattern, c, re.DOTALL)
            classes = re.findall(class_pattern, c, re.DOTALL)
            enums = re.findall(enum_pattern, c, re.DOTALL)

            for it in interfaces:
                it = it[0]
                interface_name_pattern = r'interface (.*?)\s'
                name = re.search(interface_name_pattern, it, re.DOTALL).group(1)
                with open(test_dir / f'{name}.java', 'w', encoding='utf-8') as f:
                    f.write("import org.junit.jupiter.api.Test;\nimport static org.junit.jupiter.api.Assertions.*;\n")
                    f.write("\n".join(imports) + "\n")
                    f.write(it+'\n')
                file_c += 1

            for cls in classes:
                cls = cls[0]
                class_name_pattern = r'class (.*?)\s'
                name = re.search(class_name_pattern, cls, re.DOTALL).group(1)
                with open(test_dir / f'{name}.java', 'w', encoding='utf-8') as f:
                    f.write("import org.junit.jupiter.api.Test;\nimport static org.junit.jupiter.api.Assertions.*;\n")
                    f.write("\n".join(imports) + "\n")
                    f.write(cls+'\n')
                file_c += 1

            for enum in enums:
                enum = enum[0]
                enum_name_pattern = r'enum (.*?)\s'
                name = re.search(enum_name_pattern, enum, re.DOTALL).group(1)
                with open(test_dir / f'{name}.java', 'w', encoding='utf-8') as f:
                    f.write("import org.junit.jupiter.api.Test;\nimport static org.junit.jupiter.api.Assertions.*;\n")
                    f.write("\n".join(imports) + "\n")
                    f.write(enum + '\n')
                file_c += 1

        files_for_prob_dir = input_files_path / str(_id)
        if os.path.exists(files_for_prob_dir):
            for file in os.listdir(files_for_prob_dir):
                file_for_prob = files_for_prob_dir / str(file)
                if os.path.isfile(file_for_prob):
                    shutil.copy(file_for_prob, test_dir / str(file))
                elif os.path.isdir(file_for_prob):
                    shutil.copytree(file_for_prob, test_dir / str(file))

        testcases = item['testcases']
        test_file_name = test_dir / f'Test_java_{_id}.java'
        test_file_name_pattern = fr"class (.*?)\s"
        match4 = re.search(test_file_name_pattern, testcases, re.DOTALL)
        with open(test_file_name, 'w', encoding='utf-8') as f:
            tmp = testcases.replace(match4.group(1), f'Test_java_{_id}')
            f.write(tmp)
        testrunner_file = test_dir / 'TestRunner.java'
        tr_code = Testrunner.replace('YourTestClass', f'Test_java_{_id}')
        with open(testrunner_file, 'w') as f:
            f.write(tr_code)


def write_test_files(data_dir, input_files_path, data, language, ckpt):
    os.makedirs(data_dir / ckpt, exist_ok=True)
    if language == 'python':
        write_python_test_files(data, data_dir, input_files_path, ckpt)
    elif language == 'java':
        write_java_test_files(data, data_dir, input_files_path, ckpt)
    return ckpt
