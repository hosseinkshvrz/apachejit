import json
import os.path
import argparse
import re

import requests
from github import Github
import pandas as pd
from git_token import Token
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
data_path = os.path.join(BASE_DIR, 'data')


class GithubCollector(object):

    def __init__(self):
        self.token_list = Token.get_token_list()
        self.github = Github(self.token_list[0].token)
        self.session = requests.Session()
        self.proj_repo = {'MESOS': ['apache/mesos'], 'AMQ': ['apache/activemq'], 'HBASE': ['apache/hbase'],
                          'SPARK': ['apache/spark'], 'KAFKA': ['apache/kafka'], 'GROOVY': ['apache/groovy'],
                          'ZEPPELIN': ['apache/zeppelin'], 'HDFS': ['apache/hadoop-hdfs', 'apache/hadoop'],
                          'FLINK': ['apache/flink'], 'ROCKETMQ': ['apache/rocketmq'], 'CAMEL': ['apache/camel'],
                          'MAPREDUCE': ['apache/hadoop-mapreduce', 'apache/hadoop'], 'IGNITE': ['apache/ignite'],
                          'CASSANDRA': ['apache/cassandra'], 'HIVE': ['apache/hive'], 'ZOOKEEPER': ['apache/zookeeper']}
        self.found = {}
        self.notfound = []
        self.dump_rate = 500
        Path("logs/").mkdir(parents=True, exist_ok=True)
        logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                            level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                            handlers=[
                                RotatingFileHandler(filename='logs/github_collection.log', maxBytes=5 * 1024 * 1024,
                                                    backupCount=5)])

    def dump_data(self):
        f_file = os.path.join(data_path, '{}.csv'.format(self.project.lower()))
        df = pd.DataFrame(self.found.items(), columns=['issue_key', 'commit_id'])
        df.to_csv(f_file, index=False)
        n_file = os.path.join(data_path, 'notfound.csv')
        if os.path.isfile(n_file):
            df_prev = pd.read_csv(n_file)
        else:
            df_prev = pd.DataFrame(columns=['project', 'issue_key'])
        df_new = pd.DataFrame({'project': self.project.lower(), 'issue_key': self.notfound})
        df = pd.concat([df_prev, df_new])
        df.to_csv(n_file, index=False)

    def start(self, issue_keys, project):
        self.project = project
        repos = self.proj_repo[project]
        count = 0
        for k in issue_keys:
            for r in repos:
                Token.update_token(self.github, token_list=self.token_list)
                headers = {'authorization': '{}'.format(self.github._Github__requester._Requester__authorizationHeader),
                           'content-type': 'application/json',
                           'accept': 'application/vnd.github.cloak-preview'}
                url = 'https://api.github.com/search/commits?q=repo:{}+"{}"'.format(r, k)
                while True:
                    try:
                        response = self.session.get(url, headers=headers)
                        response_dict = json.loads(response.text)
                        items = response_dict['items']
                        break
                    except:
                        time.sleep(30)
                if len(items) > 0:
                    self.found[k] = items[0]['sha']
                    break
            if k not in self.found:
                self.notfound.append(k)
            count += 1
            logging.info("Completed {:.2f} %".format((count / len(issue_keys)) * 100))
            if count % self.dump_rate == 0:
                self.dump_data()
                self.notfound = []
        self.dump_data()
        Token.dump_all_token(self.token_list)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=None, type=str, help="")
    args = parser.parse_args()
    project = args.project

    years = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019']
    dfs = []
    for y in years:
        df = pd.read_csv(os.path.join(data_path, y + '.csv'))
        print('a df of size {} appended.'.format(len(df)))
        dfs.append(df)
    df = pd.concat(dfs, axis=0, ignore_index=True)
    df.drop_duplicates(subset=['Issue key'])

    issue_keys = df[df['Issue key'].str.split('-').str[0] == project]['Issue key']

    github = GithubCollector()
    github.start(issue_keys, project)
    
