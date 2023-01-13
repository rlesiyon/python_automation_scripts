#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import json
import logging
import requests
import pprint

import multiprocessing.dummy
from subprocess import PIPE, Popen


API = 'api.github.com'
USER = None
TOKEN = None
KIND = None
DEBUG = None
ERR = None
LIMIT = 16  # M
POOL = multiprocessing.dummy.Pool(5)
PP = pprint.PrettyPrinter(indent=2)

DEFAULT_FMT = '%(levelname)-8s [%(asctime)s] %(name)s: %(message)s'

class Formatter(logging.Formatter):
    def __init__(self, datefmt=None):
        logging.Formatter.__init__(self, DEFAULT_FMT, datefmt)
        self.converter = time.gmtime

    def formatException(self, exc_info):
        text = logging.Formatter.formatException(self, exc_info)
        text = '\n'.join(('! %s' % line) for line in text.splitlines())
        return text


def get_console_logger(name):
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(Formatter())

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    return logger

def shell(command, stdin=None):
    process = Popen(
        args=command,
        stdout=PIPE,
        stderr=PIPE,
        stdin=stdin,
        shell=True,
        close_fds=True
    )
    std = process.communicate()
    if std[0]:
        DEBUG(std[0])
    if std[1]:
        ERR(std[1])
    process.wait()

def parse_options():
    global TOKEN, USER, KIND, LIMIT

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-t', dest='token', action='store', type='string',
                      default=TOKEN)
    parser.add_option('-u', dest='user', action='store', type='string',
                      help='specify the config file')
    parser.add_option('-k', dest='kind', action='store', type='string',
                      help='specify the kind')
    parser.add_option('--limit', dest='limit', action='store', type='int',
                      help='specify the limit size of clone', default=LIMIT)

    options, _ = parser.parse_args()

    assert options.token, 'token required'
    assert options.user, 'user required'
    assert options.kind, 'kind required'

    USER, TOKEN, KIND = options.user, options.token, options.kind
    if options.limit != LIMIT:
        LIMIT = options.limit


def get_headers():
    headers = {
        'Host': API,
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {TOKEN}'
    }

    return headers

def do_request(page):
    url = f'https://{API}/user/repos?type=all&per_page={page}'
    r = requests.get(url, headers=get_headers())
    return r

def shell_clone(url):
    if url.find('f22') != -1:
        DEBUG('cloning: %s' % url)
        student_path = url.rstrip('.git').split('/')[-2]
        if os.path.isdir(student_path):
            ERR(f'directory exists: {url}')
            return
        shell('git clone %s %s' % (url, student_path))

class Clone(object):
    @staticmethod
    def gists(gist):
        shell_clone(gist['git_pull_url'])

    @staticmethod
    def repos(repo):
        url = repo['clone_url']
        lang = os.environ.get('GITHUB_LANG', '').strip()
        if lang:
            lang = lang.lower().split(',')
            repo_lang = str(repo['language'])
            if repo_lang.lower() not in lang:
                DEBUG('skip: %s, language: %s' % (url, repo_lang))
                return

        if repo['size'] / 1024 > LIMIT:
            DEBUG('skip: %s, size: %d' % (url, repo['size']))
            return
        shell_clone(url)


def clone(tasks):
    POOL.map(getattr(Clone, KIND), tasks)


def fetch(page=0):
    page += 1
    r = do_request(page)
    if r is None:
        return

    DEBUG('get page: %d, status: %d, content length: %d' % (
          page, r.status_code, len(r.content)))

    tasks = json.loads(r.content)
    if tasks:
        clone(tasks)
        fetch(page)


def main():
    global DEBUG, ERR
    logger = get_console_logger('git/clone-it')
    DEBUG = lambda s: logger.log(logging.DEBUG, s)
    ERR = lambda s: logger.log(logging.ERROR, s)

    parse_options()
    fetch()
    
if __name__ == '__main__':
    main()