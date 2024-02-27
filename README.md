# NaturalCodeBench: A Challenging Application-Driven Dataset for Code Synthesis Evaluation

This repository contains information, data and code of NaturalCodeBench: A Challenging Application-Driven Dataset for Code Synthesis Evaluation.

## 📌Introduction

Current benchmarks for code synthesis, such as HumanEval, MBPP, and DS-1000, are predominantly oriented towards introductory algorithmic and data science tasks, and do not adequately encompass the diverse requirements prevalent in real coding scenarios, like operating systems, and front-end devloping, and software engineering. To fill this gap, we propose  NaturalCodeBench (NCB), a comprehensive code benchmark designed to mirror the complexity and variety of scenarios in real coding tasks. NCB comprises 402 high-quality problems in Python and Java, meticulously selected from an online coding service, covering seven different domains. We also introduce a semi-automated pipeline that leverages GPT-4 to enhance the efficiency of test case construction. Our semi-automated pipeline, when compared experimentally with manually written reference solutions and test cases, exhibits a substantial efficiency improvement, achieving an increase of more than four times.We conduct systematic experiments on 31 LLMs and find that performance gaps on \model between models with close HumanEval scores could still be significant, indicating a lack of optimization on practical code synthesis scenarios. At the same time, even the best-performing GPT-4 is still far from perfect.

![overview](C:\Users\Daniel\Downloads\overview.png)

The overall framework of NaturalCodeBench is shown in the above image, including the data collection pipeline and the semi-automated pipeline.

For a full description of NaturalCodeBench, please refer to the paper: 

## Dataset Summary

To construct a challenging application-driven dataset for code synthesis evaluation, the seed problems of NCB are cleaned from the queries in coding online services, spanning across 7 domains: Database, Artificial Intelligence, Data Science, Algorithm and Data Structure, Front-End, Software Engineering, and Operation System.

<table style="width: 50%;">
    <tr>
        <td rowspan="2" style="width: 400px;"><strong>Domains</strong></td>
        <td colspan="3" align="center"><strong>#Problems</strong></td>
    </tr>
    <tr>
        <td align="center"><strong>Dev</strong></td>
        <td align="center"><strong>Test</strong></td>
        <td align="center"><strong>Total</strong></td>
    </tr>
    <tr>
        <td>Software Engineering</td>
        <td align="center">44</td>
        <td align="center">88</td>
        <td align="center">132</td>
    </tr>
    <tr>
        <td>Data Science</td>
        <td align="center">32</td>
        <td align="center">68</td>
        <td align="center">100</td>
    </tr>
    <tr>
        <td>Algorithm and Data Structure</td>
        <td align="center">22</td>
        <td align="center">73</td>
        <td align="center">95</td>
    </tr>
    <tr>
        <td>Artificial Intelligence</td>
        <td align="center">15</td>
        <td align="center">13</td>
        <td align="center">28</td>
    </tr>
    <tr>
        <td>Operation System</td>
        <td align="center">15</td>
        <td align="center">12</td>
        <td align="center">27</td>
    </tr>
    <tr>
        <td>Front-End</td>
        <td align="center">11</td>
        <td align="center">3</td>
        <td align="center">14</td>
    </tr>
    <tr>
        <td>Database</td>
        <td align="center">1</td>
        <td align="center">5</td>
        <td align="center">6</td>
    </tr>
</table>

NaturalCodeBench contains 402 high-quality problems in total. We release the development set of NCB, which contains 140 problems (70 in Python and 70 in Java) for research purpose. The data is placed in ...

The data format is as follows.

- ```_id```(integer): A unique identifier for each question.
- ```prompt```(string): The prompt involving problem description and instruction.
- ```problem```(string): The problem description
- ```testcases```(string): The code of testcases
- ```setup_code```(string): The code for test setup
- ```reference_solution```(string): A reference answer to solve the problem.
- ```classification```(string): The domain of the problem

## Installation

| Dependency | Version  |
| ---------- | -------- |
| Python     | 3.10.13  |
| JDK        | 18.0.2.1 |

Clone this repo and install the dependencies. Make sure to use python 3.10.13 or later:

```bash
conda create -n ncb python=3.10.13
conda activate ncb
git clone https://github.com/Daniel-0222/NaturalCodeBench
cd NaturalCodeBench
pip install -r requirements.txt
```

### Docker

We strongly recommend you to use docker to setup the environment. Firstly pull the image.

```
docker pull codegeex/codegeex:0.2.22
```

Then start Docker and mount the code directory.

```bash
docker run --rm -it --shm-size 32g -v /path/to/NaturalCodeBech:/ncb codegeex/codegeex:0.1.22 /bin/bash
```

## Usage

Generate samples and save them in the following JSON Lines (jsonl) format, where each sample is formatted into a single line like so:

```
{"_id": "NaturalCodeBench Problem ID", "response": "The response of model without prompt"}
```

Place your JSONL files into the `result` directory according to the following directory structure.

```
results/
└── {model_name}/
    ├── {model_name}_ncb_java_en.jsonl
    ├── {model_name}_ncb_java_zh.jsonl
    ├── {model_name}_ncb_python_en.jsonl
    └── {model_name}_ncb_python_zh.jsonl
```

We provide `reference`  under `results` to illustrate the format and help with debugging.

To evaluate the samples, run

```
python ncb/evaluate.py --languages python java --natural_lang zh en --ckpt_name {your_model_name} --num_workers 64 --ks 1 10 100
```

