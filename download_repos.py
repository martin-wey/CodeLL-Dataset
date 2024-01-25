import argparse
import os
import sys
import time
import requests
import logging

import pandas as pd
from tqdm import tqdm

from swh_miner import TOKEN
from swh_utils import get_request_header

tqdm_kwargs = {
    'bar_format': '{l_bar}{bar:100}{r_bar}{bar:-10b}',
    'file': sys.stdout
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--download_data_fp", default="download_data.csv", type=str)
    parser.add_argument("--output_dir", default=None, type=str)
    args = parser.parse_args()

    logging.basicConfig(
        filename=f'{args.output_dir}/download.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    os.makedirs(args.output_dir, exist_ok=True)
    data = pd.read_csv(args.download_data_fp)

    n = 0
    n_download = 0
    for index, row in tqdm(data.iterrows(), total=len(data), **tqdm_kwargs):
        repository_url = row['repository']
        if 'github' in repository_url or 'gitlab' in repository_url:
            repo_name = repository_url.split('/')[-1]
        else:
            repo_name = repository_url.split('/')[-2]
        repo_dir = f'{args.output_dir}/{repo_name}'

        if not os.path.exists(repo_dir):
            os.makedirs(repo_dir, exist_ok=True)

        repo_branch = row['branch'].replace('/', '-')
        repo_branch_dir = f'{repo_dir}/{repo_branch}'

        if os.path.exists(f'{repo_branch_dir}/data.tar.gz'):
            continue
        os.makedirs(repo_branch_dir, exist_ok=True)

        try:
            header = get_request_header(TOKEN)
            response = requests.get(row['download_link'], headers=header)
            with open(f'{repo_branch_dir}/data.tar.gz', 'wb') as file:
                file.write(response.content)
        except Exception as e:
            logging.info(f"Error downloading {row['download_link']}: {e}")

        n_download += 1
        # avoid too many requests error on SH API
        if n_download % 25 == 0:
            time.sleep(5)
