import argparse
import contextlib
import csv
import json
import random
import re
import string
from pathlib import Path

from mimesis import Algorithm, Cryptographic, Datetime, Food, Internet, Text
from mimesis.enums import TimestampFormat

RF_IDs = ('ip:', 'idn:', 'hash:', 'url:')
ISO_8601_REGEX = re.compile(
    r'^(\d{4})-(\d{2})-(\d{2})'
    r'T(\d{2}):(\d{2}):(\d{2})'
    r'(?:\.(\d+))?'
    r'(Z|[+-]\d{2}:\d{2})?$'
)

DATE_REGEX = re.compile(r'^(\d{4})-(\d{2})-(\d{2})')
URL_REGEX = re.compile(r'^http[s]://')
RFID = re.compile(r'^[\w_-]{4,6}$')
IP_REGEX = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
DOMAIN_REGEX = re.compile(
    r'^(?:[a-zA-Z0-9]' r'(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+' r'[a-zA-Z]{2,}$'
)

DO_NOT_CHANGE = ('type', 'status', 'algorithm', 'category', 'playbook_alert_id')


def _make_obfuscation(value, key):
    text = Text()
    food = Food()
    if isinstance(value, str):
        match key:
            case 'id':
                if value.startswith('ip:'):
                    return f'ip:{Internet().ip_v4()}'
                if value.startswith('idn:'):
                    return f'idn:{Internet().hostname()}'
                if value.startswith('url:'):
                    return f'url:{Internet().url()}'
                if value.startswith('hash:'):
                    return f'hash:{Cryptographic().hash(algorithm=Algorithm.SHA256)}'
                if value.startswith('report:'):
                    return value
                return ''.join(random.choices(string.ascii_letters + string.digits, k=len(value)))  # noqa: S311
            case 'title':
                return text.title()
            case 'name':
                return food.dish()
            case 'text':
                return text.text()

            # dont change them
            case _ if key in DO_NOT_CHANGE:
                return value

        match value:
            case v if re.match(ISO_8601_REGEX, v):
                return Datetime().timestamp(fmt=TimestampFormat.ISO_8601)[:-3] + 'Z'
            case v if re.match(DATE_REGEX, v):
                return '2024-02-02'
            case v if re.match(URL_REGEX, v):
                return Internet().url()
            case v if re.match(IP_REGEX, v):
                return Internet().ip_v4()
            case v if re.match(DOMAIN_REGEX, v):
                return Internet().hostname()
            case _:
                return text.text(quantity=1)
    return value


def obfuscate(data, key=None):
    if isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k] = obfuscate(v, key=k)
        return new_data
    if isinstance(data, list):
        return [obfuscate(v, key=key) for v in data]

    if isinstance(data, (str, int)):
        return _make_obfuscation(data, key=key)

    return data


def obfuscate_json(file, original_data):
    print('-------------------- BEFORE -------------')

    print(json.dumps(original_data, indent=4))
    print('\n\n')
    print('-------------------- AFTER -------------')
    sanitized_data = obfuscate(original_data)

    print(json.dumps(sanitized_data, indent=4))

    original_file = Path(file.as_posix().replace(file.suffix, f'{file.suffix}_ORIGINAL'))
    original_file.write_text(json.dumps(original_data, indent=4))
    file.write_text(json.dumps(sanitized_data, indent=4))


def obuscate_csv(file, rows):
    print('-------------------- BEFORE -------------')
    print(json.dumps(rows, indent=4))
    print('\n\n')
    print('-------------------- AFTER -------------')

    obfuscated_rows = obfuscate(rows)
    print(json.dumps(obfuscated_rows, indent=4))

    def flatten_json(val):
        if isinstance(val, (dict, list)):
            return json.dumps(val)
        return val

    with contextlib.suppress(IndexError):  # file is empty
        with file.open('w', newline='', encoding='utf-8') as out_csv:
            writer = csv.DictWriter(out_csv, fieldnames=obfuscated_rows[0].keys())
            writer.writeheader()
            for row in obfuscated_rows:
                flat_row = {k: flatten_json(v) for k, v in row.items()}
                writer.writerow(flat_row)

        original_file = Path(file.as_posix().replace(file.suffix, f'{file.suffix}_ORIGINAL'))
        with original_file.open('w', newline='', encoding='utf-8') as orig_csv:
            writer = csv.DictWriter(orig_csv, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                flat_row = {k: flatten_json(v) for k, v in row.items()}
                writer.writerow(flat_row)


def main():
    parser = argparse.ArgumentParser(description='Input mock for sanitization')
    parser.add_argument('-i', '--input', type=Path, required=True, help='Input file or folder')
    args = parser.parse_args()
    p = args.input.resolve()

    if not p.exists():
        print('Path does not exist.')
        exit(1)

    files_to_process = []

    if p.is_file():
        if p.suffix.lower() in ('.json', '.csv'):
            files_to_process.append(p)
        else:
            print(f'Unsupported file type: {p.suffix}')
            exit(1)
    elif p.is_dir():
        files_to_process.extend(p.glob('*.json'))
        files_to_process.extend(p.glob('*.csv'))
    else:
        print('Input must be a file or directory.')
        exit(1)

    for file in files_to_process:
        if file.is_dir():
            continue
        if file.suffix == '.json':
            original_data = json.loads(file.read_text())
            obfuscate_json(file, original_data)

        elif file.suffix == '.csv':
            rows = []
            with file.open(newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    for key, val in row.items():
                        try:
                            parsed_val = json.loads(val)
                            row[key] = parsed_val
                        except (json.JSONDecodeError, TypeError):
                            pass
                    rows.append(row)

                obuscate_csv(file, rows)
        else:
            print('unknown file type')


if __name__ == '__main__':
    main()
