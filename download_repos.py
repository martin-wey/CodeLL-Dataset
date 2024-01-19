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

    for index, row in tqdm(data.iterrows(), total=len(data), **tqdm_kwargs):
        # avoid too many requests error on SH API
        if index % 10 == 0:
            time.sleep(5)

        repository_url = row['repository']
        if 'github' in args.download_data_fp or 'gitlab' in args.download_data_fp:
            repo_name = repository_url.split('/')[-1]
        else:
            repo_name = repository_url.split('/')[-2]
        repo_dir = f'{args.output_dir}/{repo_name}'
        os.makedirs(repo_dir, exist_ok=True)

        repo_branch = row['branch'].replace('/', '-')
        repo_branch_dir = f'{repo_dir}/{repo_branch}'
        os.makedirs(repo_branch_dir, exist_ok=True)

        try:
            header = get_request_header(TOKEN)
            response = requests.get(row['download_link'], headers=header)
            with open(f'{repo_branch_dir}/data.tar.gz', 'wb') as file:
                file.write(response.content)
        except Exception as e:
            logging.info(f"Error downloading {row['download_link']}: {e}")
