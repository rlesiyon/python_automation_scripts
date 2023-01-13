import argparse
import pprint
import sys

import requests
from requests.auth import HTTPBasicAuth


def repos_invitation_requests(github_token):

    url = 'https://api.github.com/user/repository_invitations'
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {github_token}'
    }
    return requests.get(
                url, headers= headers).json()

def accept_invite(repo_id, login, github_token):

    requests.patch('https://api.github.com/user/repository_invitations/{}'.format(repo_id),
                        data={}, headers={},
                   auth=HTTPBasicAuth(login, github_token))

def main():

    args = command_line(sys.argv)
    repos_contributors = []
    
    for repository_invite in repos_invitation_requests(args.github_token):
        repository_id = repository_invite.get('id')
        owner, repo = repository_invite.get('repository').get('full_name').split('/')
        contributors_url = f'https://api.github.com/repos/{owner}/{repo}/collaborators'

        # Patch to accept the invite.
        accept_invite(repository_id, args.login, args.github_token)

        # get repo contributors    
        repo_contributors = requests.get(
                contributors_url, auth=HTTPBasicAuth(args.login, args.github_token)).json()

        repo_contributors.append(f'{owner}, {repo_contributors}')

    with open('repos_contributors.txt', 'w') as fp:
        for repo_contributor in repos_contributors:
            fp.write(repo_contributors + "\n")

def command_line(argv):
    
    parser = argparse.ArgumentParser(
        description= 'Get all the invites sent to my repo and accept them', 
        add_help=True,
    )
    parser.add_argument('-g', '--github_token')
    parser.add_argument('-l', '--login')

    return parser.parse_args()

if __name__ == "__main__":
    main()    
