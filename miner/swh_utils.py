import http.client
import time

import requests


SEARCH_VAULT = "https://archive.softwareheritage.org/api/1/vault/directory/"
SEARCH_ORIGINS = "https://archive.softwareheritage.org/api/1/origin/"
SEARCH_SNAPSHOT = "https://archive.softwareheritage.org/api/1/snapshot/"


def get_request_header(token):
    return {'Authorization': f'Bearer {token}'}


def run_request(url, auth_token, request_type='get', max_attempts=5):
    request_func = getattr(requests, request_type)

    for attempt in range(max_attempts):
        try:
            header = get_request_header(auth_token)
            response = request_func(url, headers=header)
            if response.status_code == 200:
                return response
            elif response.status_code == 404:
                print(f'[404] - URL {url} not found.')
                break
            elif response.status_code == 500:
                print(f'[500] - Could not process request.')
            elif response.status_code == 429:
                print(f'Too many requests.')
                time.sleep(1000)
        except (http.client.RemoteDisconnected, requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout,
                requests.exceptions.SSLError):
            pass

    return None


def get_repo_releases_branches(origin, auth_token):
    repo_snapshot = run_request(f'{SEARCH_ORIGINS}{origin}/visit/latest/', auth_token=auth_token)

    if repo_snapshot is not None:
        repo_snapshot_content = repo_snapshot.json()
        repo_release_branches = run_request(f'{SEARCH_SNAPSHOT}{repo_snapshot_content["snapshot"]}',
                                            auth_token=auth_token)
        if repo_release_branches is not None:
            repo_release_branches_content = repo_release_branches.json()
            return repo_release_branches_content

    return None


def get_download_url(target_url, auth_token):
    release_data = run_request(target_url, auth_token)

    if release_data is not None:
        release_data_content = release_data.json()
        if isinstance(release_data_content, list):
            return None, None, None
        release_id = release_data_content.get('target', release_data_content.get('directory'))
        release = run_request(f'{SEARCH_VAULT}{release_id}/', auth_token=auth_token, request_type='post')
        release_name = release_data_content.get('name', 'None')
        release_date = release_data_content.get('date', 'None')

        if release is not None:
            release_content = release.json()
            return release_content['fetch_url'], release_name, release_date

    return None, None, None
