import argparse
import csv
import os.path
import re
import sys
import time

import swh_utils as swh

TOKEN = "your software heritage token"
version_regex = r'(v?\d+\.\d+(\.\d+)*)'

tqdm_kwargs = {
    'bar_format': '{l_bar}{bar:100}{r_bar}{bar:-10b}',
    'file': sys.stdout
}


def fetch_repo_urls(origin, auth_token):
    data = []
    # get all the revisions for the current repo
    releases = swh.get_repo_releases_branches(origin, auth_token)

    if releases is None or 'branches' not in releases or releases['branches'] == {}:
        print(f'Could not find any release for the repository {origin}.')
        return data

    for branch_id, branch_data in releases['branches'].items():
        # ignoring pull requests
        if "pull" in branch_id:
            continue
        # ignoring branches that are not versions
        match = re.search(version_regex, branch_id)
        if match and branch_data['target_type'] == 'release' and ('github.com' in origin or 'gitlab' in origin):
            revision_data = swh.run_request(branch_data['target_url'], auth_token=auth_token)
            revision_data_content = revision_data.json()
            target_url = revision_data_content['target_url']
        else:
            target_url = branch_data['target_url']

        print(f'-- Fetching {origin} - branch {branch_id}')

        url, name, date = swh.get_download_url(target_url, auth_token)
        if url is not None:
            data.append((branch_id, url, name, date))
        print('-' * 100)

    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", type=str, default=None)
    args = parser.parse_args()

    output_file = os.path.join(os.path.dirname(args.input_file), 'download_data_raw.csv')

    with open(args.input_file, 'r') as f:
        repos_set = [url.strip() for url in f.readlines()]

    with open(output_file, 'w', newline='') as fout:
        writer = csv.writer(fout)
        writer.writerow(['repository', 'branch', 'download_link', 'name', 'date'])

        for origin in repos_set:
            repo_releases_data = fetch_repo_urls(origin, TOKEN)

            if not repo_releases_data:
                writer.writerow([origin, 'None', 'None', 'None', 'None'])
            else:
                for id, url, name, date in repo_releases_data:
                    writer.writerow([origin, id, url, name, date])

            # avoid too many requests error
            time.sleep(10)
