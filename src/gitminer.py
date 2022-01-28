import argparse
import os
import pickle

import pandas as pd
from pydriller import Repository, Git
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
data_path = os.path.join(BASE_DIR, 'data')


class GitMiner:
    def __init__(self):
        self.repo_dir = os.path.join(BASE_DIR, 'repos')
        self.proj_repo = {'AMQ': ['apache/activemq'], 'CAMEL': ['apache/camel'], 'CASSANDRA': ['apache/cassandra'],
                          'FLINK': ['apache/flink'], 'GROOVY': ['apache/groovy'], 'HBASE': ['apache/hbase'],
                          'HDFS': ['apache/hadoop-hdfs', 'apache/hadoop'], 'HIVE': ['apache/hive'],
                          'IGNITE': ['apache/ignite'], 'KAFKA': ['apache/kafka'],
                          'MAPREDUCE': ['apache/hadoop-mapreduce', 'apache/hadoop'], 'SPARK': ['apache/spark'],
                          'ZEPPELIN': ['apache/zeppelin'], 'ZOOKEEPER': ['apache/zookeeper']}

        Path("logs/").mkdir(parents=True, exist_ok=True)
        logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                            level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                            handlers=[
                                RotatingFileHandler(filename='logs/pydriller.log', maxBytes=5 * 1024 * 1024,
                                                    backupCount=5)])

    def run_collector(self, df, project):
        data = {'fix_hash': [], 'fix_date': [], 'bug_hash': [], 'bug_date': [], 'project': []}
        project_df = df[df['project'] == project]
        fix_commits = project_df['commit_id'].tolist()
        repos = [os.path.join(self.repo_dir, r.split('/')[-1]) for r in self.proj_repo[project]]
        count = 0
        for commit in Repository(repos,
                                 only_commits=fix_commits).traverse_commits():
            git = Git(commit.project_path)
            szz = git.get_commits_last_modified_lines(commit)
            bug_inducing = set(c for sublist in [*szz.values()] for c in sublist)
            for b in bug_inducing:
                data['fix_hash'].append(commit.hash)
                data['fix_date'].append(int(commit.committer_date.timestamp()))
                data['bug_hash'].append(b)
                data['bug_date'].append(int(git.get_commit(b).committer_date.timestamp()))
                data['project'].append(project)
            count += 1
            logging.info('Completed {:.2f} %'.format((count / len(fix_commits)) * 100))

        return data

    def collect_clean(self):
        repos = [os.path.join(self.repo_dir, r.split('/')[-1]) for r in
                 [c for sublist in [*self.proj_repo.values()] for c in sublist]]
        all_commits = pd.read_csv(os.path.join(data_path, 'bug_fix_all.csv'))['commit_id'].tolist()
        clean_commits, projects, dates = [], [], []
        count = 0
        for commit in Repository(repos,
                                 # start and date from notebook (the earliest buggy commit)
                                 since=datetime.datetime(2003, 9, 11, 14, 11, 56),
                                 # end date from notebook (the latest buggy commit because it's earlier than bug-fix median diff)
                                 to=datetime.datetime(2019, 12, 26, 18, 29, 9)).traverse_commits():
            if commit.hash not in all_commits:
                clean_commits.append(commit.hash)
                projects.append('apache/{}'.format(commit.project_name))
                dates.append(int(commit.committer_date.timestamp()))
                if len(clean_commits) % 1000 == 0:
                    pd.DataFrame({'commit_id': clean_commits, 'project': projects, 'commit_date': dates})\
                        .to_csv(os.path.join(data_path, 'clean.csv'), index=False)
                    logging.info('{} commits visited, len(clean_commits)={}'.format(count, len(clean_commits)))
                    logging.info('current commit date: {}'.format(commit.committer_date.strftime("%b %d, %Y")))
            count += 1
        pd.DataFrame({'commit_id': clean_commits, 'project': projects, 'commit_date': dates}) \
            .drop_duplicates().to_csv(os.path.join(data_path, 'clean.csv'), index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=None, type=str, help="")
    args = parser.parse_args()
    project = args.project
    df = pd.read_csv(os.path.join(data_path, 'found.csv'))
    miner = GitMiner()
    data = miner.run_collector(df, project)
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(data_path, 'commit_links_{}.csv'.format(project)), index=False)
    print('{} finished.'.format(project))
    miner.collect_clean()
    print('finished.')
