import subprocess
import shutil
import os
import json
import argparse

from datetime import datetime


parser = argparse.ArgumentParser()
parser.add_argument('-a', '--analyze', action='store_true', help="Analyze the repos in input.json")
parser.add_argument('-m', '--manual-check', action='store_true',
                    help="Analyze all repos in dir 'manual_check'. It is expected that these have "
                         "manually been setup for analysis.")
parser.add_argument('-c', '--cleanup', action='store_true', help="Cleanup after analysis")


class JSONHandler:

    def __init__(self, file_to_handle: str):
        self.FILE = file_to_handle

        if not os.path.exists(self.FILE):
            with open(self.FILE, 'w') as f:
                f.write(json.dumps({self.FILE.split('.')[0]: []}, indent=4))

    def get_file_dict(self) -> json:
        with open(self.FILE, 'r') as f:
            return json.loads(f.read())

    def write_to_file(self, data: json):
        with open(self.FILE, 'w') as f:
            f.write(json.dumps(data, indent=4))


class Repo:

    def __init__(self, url: str = None, manual_dict: dict = None):

        if url:
            self.url = url

            split = url.split('/')
            self.repo_name = split[-1]
            self.maintainer = split[-2]

            self.detected_smells = None
            self.checked_manually = False
        elif manual_dict:
            self.url = manual_dict['url']
            self.repo_name = manual_dict['repo_name']
            self.maintainer = manual_dict['maintainer']
            self.detected_smells = manual_dict['detected_smells']
            self.checked_manually = manual_dict['checked_manually']
        else:
            print('Error: object Repo init called without input')
            exit(1)

    def as_dict(self) -> dict:
        return {
            'url': self.url,
            'repo_name': self.repo_name,
            'maintainer': self.maintainer,
            'detected_smells': self.detected_smells,
            'checked_manually': self.checked_manually
        }


class RepoAnalyzer:
    URL_BASE = 'https://github.com'

    def __init__(self):
        self.output_dir = datetime.now().strftime("%d%m%Y")
        self.input_handler = JSONHandler('input.json')
        self.approved_handler = JSONHandler('approved.json')
        self.denied_handler = JSONHandler('denied.json')
        self.manual_handler = JSONHandler('manual_check.json')

        if args.analyze:
            self.repos = [Repo(url=r)
                          for r in self.input_handler.get_file_dict()['repos']]
        elif args.manual_check:
            self.repos = [Repo(manual_dict=r)
                          for r in self.manual_handler.get_file_dict()['manual_check']]
        else:
            self.repos = []

    def run(self):
        if args.analyze:
            self._analyze()

        if args.manual_check:
            self._analyze_manual()

        if args.cleanup:
            self._cleanup()

    def _analyze(self):
        print(f'Analyzing {len(self.repos)} repositories')
        count = len(self.repos)

        for repo in self.repos:
            print(f'Retreiving repo {repo.url}')
            self._setup_repo(repo)

            print('Analyzing for code smells..')
            self._analyze_repo(repo)

            print('Checking results..')
            self._check_results(repo)

            count -= 1
            if count > 0:
                print(f'{count} repos to go')
            else:
                print('Done!')

    def _analyze_manual(self):
        print(f'Analyzing {len(self.repos)} repositories')
        count = len(self.repos)

        for repo in self.repos:
            loc = f'manual_check/{repo.repo_name}'
            print(f'Processing repo at ./{loc}/')

            print('Analyzing for code smells..')
            subprocess.run(['bash', 'run-codeql.sh', loc], capture_output=True)

            print('Checking results..')
            self._check_manual_results(repo)

            count -= 1
            if count > 0:
                print(f'{count} repos to go')
            else:
                print('Done!')

        self._join_approved()

    def _cleanup(self):
        os.makedirs(f'{self.output_dir}/codeql', exist_ok=True)
        print(f'Created output dir at ./{self.output_dir}/')

        if not args.manual_check:
            print(f'Moving JSON files')
            if os.path.exists('approved.json'):
                shutil.move('approved.json', self.output_dir)
            if os.path.exists('denied.json'):
                shutil.move('denied.json', self.output_dir)
            if os.path.exists('input.json'):
                shutil.move('input.json', self.output_dir)

        print(f'Moving result files to ./{self.output_dir}/codeql/ and cleaning up repos')
        for repo in os.listdir('approved'):
            repo_dir = f'approved/{repo}'
            shutil.move(f'{repo_dir}/res.csv', f'{self.output_dir}/codeql/{repo}.csv')

            shutil.rmtree(repo_dir)

    @staticmethod
    def _setup_repo(r: Repo):
        subprocess.run(['git', 'clone', r.url], capture_output=True)
        shutil.copyfile('codeql.sh', f'{r.repo_name}/codeql.sh')

    @staticmethod
    def _analyze_repo(r: Repo):
        subprocess.run(['bash', 'run-codeql.sh', r.repo_name], capture_output=True)

    def _check_results(self, r: Repo):
        if os.path.exists(f'{r.repo_name}/res.csv'):
            with open(f'{r.repo_name}/res.csv') as f:
                contents = f.readlines()
        else:
            print(f'Repo {r.url} did not produce a results file, file tree may be borked. '
                  f'Please check manually.')
            self._add_to_manual_check(r)
            return

        r.detected_smells = len(contents)

        if contents:
            print(f'Repo {r.url} contains {len(contents)} detections, moving to approved')
            self._add_to_approved(r)
        else:
            print(f'Repo {r.url} did not contain any code smells, removing')
            self._add_to_denied(r)

    def _check_manual_results(self, r: Repo):
        if os.path.exists(f'manual_check/{r.repo_name}/res.csv'):
            with open(f'manual_check/{r.repo_name}/res.csv') as f:
                contents = f.readlines()
        else:
            print(f'Repo {r.url} did not produce a results file, file tree may be borked. '
                  f'Please check manually.')
            return

        r.detected_smells = len(contents)
        r.checked_manually = True

        if contents:
            print(f'Repo {r.url} contains {len(contents)} detections, moving to approved')
            self._add_to_approved_manual(r)
        else:
            print(f'Repo {r.url} did not contain any code smells, removing')
            self._add_to_denied(r)

    def _add_to_manual_check(self, r: Repo):
        shutil.move(r.repo_name, f'manual_check/{r.repo_name}')
        manual_dict = self.manual_handler.get_file_dict()
        manual_dict['manual_check'].append(r.as_dict())
        self.manual_handler.write_to_file(manual_dict)

    def _add_to_manual_check_second_pass(self, r: Repo):
        manual_dict = self.manual_handler.get_file_dict()
        manual_dict['second_pass'].append(r.as_dict())
        self.manual_handler.write_to_file(manual_dict)

    def _add_to_approved(self, r: Repo):
        shutil.move(r.repo_name, f'approved/{r.repo_name}')
        approved_dict = self.approved_handler.get_file_dict()
        approved_dict['approved'].append(r.as_dict())
        self.approved_handler.write_to_file(approved_dict)

    def _add_to_approved_manual(self, r: Repo):
        shutil.move(f'manual_check/{r.repo_name}', f'approved/{r.repo_name}')
        approved_dict = self.approved_handler.get_file_dict()
        approved_dict['approved'].append(r.as_dict())
        self.approved_handler.write_to_file(approved_dict)

    def _add_to_denied(self, r: Repo):
        os.rmdir(r.repo_name)
        denied_dict = self.denied_handler.get_file_dict()
        denied_dict['denied'].append(r.as_dict())
        self.denied_handler.write_to_file(denied_dict)

    def _join_approved(self):
        old_handler = JSONHandler(f'{self.output_dir}/approved.json')
        new = self.approved_handler.get_file_dict()
        old = old_handler.get_file_dict()

        for row in new['approved']:
            old['approved'].append(row)

        old_handler.write_to_file(old)
        os.remove('approved.json')


if not os.path.exists('approved'):
    os.mkdir('approved')
if not os.path.exists('manual_check'):
    os.mkdir('manual_check')

args = parser.parse_args()

if args.analyze and not os.path.exists('input.json'):
    print('Error: file input.json does not exist and is required, '
          'please see README.MD for more info')
    exit(1)

analyzer = RepoAnalyzer()
analyzer.run()