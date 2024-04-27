# NaturalCodeBench: A Challenging Application-Driven Dataset for Code Synthesis Evaluation

This repository contains information, data and code of NaturalCodeBench: A Challenging Application-Driven Dataset for Code Synthesis Evaluation.

## 📌Introduction

We propose  NaturalCodeBench (NCB), a comprehensive code benchmark designed to mirror the complexity and variety of scenarios in real coding tasks. NCB comprises 402 high-quality problems in Python and Java, meticulously selected from an online coding service, covering seven different domains. 

![overview](https://github.com/Daniel-0222/NaturalCodeBench/blob/dev/assets/overview.png)

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

We provide a docker to setup the environment. Firstly pull the image.

```
docker pull codegeex/codegeex:0.1.23
```

Then start Docker and mount the code directory.

```bash
docker run --rm -it --shm-size 32g -v /path/to/NaturalCodeBench:/ncb codegeex/codegeex:0.1.23 /bin/bash
```

Copy data into repository.

```
cd /ncb
cp -r /NaturalCodeBench/data .
```

## Usage

Generate samples and save them in the following JSON Lines (jsonl) format, where each sample is formatted into a single line like so:

```
{"_id": "NaturalCodeBench Problem ID", "response": "The response of model without prompt"}
```

Place your JSONL files into the `results` directory according to the following directory structure.

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



## Leaderboard

We report  our evaluation results of 31 LLMs on the test and dev datasets.

Test set results:

![overview](https://github.com/Daniel-0222/NaturalCodeBench/blob/dev/assets/test_set_results.png)



Dev set result:

![overview](https://github.com/Daniel-0222/NaturalCodeBench/blob/dev/assets/dev_set_results.png)
