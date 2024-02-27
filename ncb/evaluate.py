import argparse
import os
from pathlib import Path
from test_setup import write_test_files, extract_codes
from execution import execution
from utils import load_json, load_jsonl, save_json, save_jsonl, del_file


def evaluate_code(data_dir, language, natural_lang, ckpt_name, ks, num_workers=64):
    file = f'results/{ckpt_name}/{ckpt_name}_ncb_{language}_{natural_lang}.jsonl'
    print(file)
    os.makedirs(data_dir, exist_ok=True)
    del_file(data_dir / f'{ckpt_name}')

    data = load_jsonl(file)
    dataset_size = len(data)
    testcases = load_jsonl(f'data/{language}_{natural_lang}/ncb_{language}_{natural_lang}.jsonl')

    print("Extracting code from response")
    data = extract_codes(data, testcases, language)

    print("Writing test files")
    input_files_path = Path(f'data/{language}_{natural_lang}/input_files')
    test_dir = write_test_files(data_dir, input_files_path, data, language, ckpt_name)

    print("Start evaluation")
    result = execution(data_dir / test_dir, ckpt_name, language, natural_lang, dataset_size, ks, num_workers)
    print(result, '\n')
    save_json(result, data_dir / test_dir / 'result.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--languages', type=str, nargs='+', default=['python', 'java'], help='programming language')
    parser.add_argument('--natural_langs', type=str, nargs='+', default=['zh', 'en'], help='natural language')
    parser.add_argument('--ckpt_name', type=str, required=True, default='reference', help='the name of ckpt that you want to evaluate')
    parser.add_argument('--num_workers', type=int, default=64, help='number of workers')
    parser.add_argument('--ks', type=int, nargs='+', default=[1], help='k of the pass@k')
    args = parser.parse_args()

    results = []
    for nat_lang in args.natural_langs:
        for lang in args.languages:
            data_dir = Path(f'data/temp/{lang}_{nat_lang}_test')
            evaluate_code(data_dir, lang, nat_lang, args.ckpt_name, args.ks, args.num_workers)
            results.append(load_json(data_dir / f'{args.ckpt_name}/result.json'))
    save_jsonl(results, f'results/{args.ckpt_name}/results.jsonl')
    for res in results:
        print(res)
