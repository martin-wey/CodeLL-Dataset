import argparse
import json
import logging
import os
import sys

import pandas as pd

from comparators import RepositoryComparator
from parser import Repository

tqdm_kwargs = {
    'bar_format': '{l_bar}{bar:100}{r_bar}{bar:-10b}',
    'file': sys.stdout
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default=None)
    parser.add_argument('--download_data_fp', type=str, default=None)
    parser.add_argument('--output_dir', type=str, default=None)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{args.output_dir}/data_generator.log'),
            logging.StreamHandler()
        ]
    )

    os.makedirs(args.output_dir, exist_ok=True)
    metadata_df = pd.read_csv(args.download_data_fp)

    # convert to get identical naming conventions used in the data directory
    metadata_df['repository_name'] = metadata_df['repository'].apply(
        lambda v: v.split('/')[-1] if 'github' in v else v.split('/')[-2])
    metadata_df['branch'] = metadata_df['branch'].apply(lambda v: v.replace('/', '-'))
    metadata_df['date'] = pd.to_datetime(metadata_df['date'], utc=True)
    metadata_df = metadata_df.drop(['download_link', 'name'], axis=1)

    # split dataframe in a list of dataframe (one per repository)
    df_list = [group.reset_index(drop=True) for _, group in metadata_df.groupby('repository_name')]

    for repo_df in df_list:
        repository_name = str(repo_df['repository_name'].iloc[0])
        repository_dir = os.path.join(args.data_dir, repository_name)
        if not os.path.exists(repository_dir):
            logging.info(f'Repository directory does not exist: {repository_dir}')
            continue

        logging.info(f'Extracting data from `{repository_name}`')
        with open(f'{args.output_dir}/{repository_name}.jsonl', 'w') as fout:
            for index, row in repo_df.iterrows():
                release_dir_current = os.path.join(args.data_dir, row['repository_name'], row['branch'])
                if not os.path.exists(release_dir_current):
                    logging.info(f'Release directory does not exist: {release_dir_current}')
                    continue

                row["date"] = str(row["date"])
                if index + 1 < len(repo_df):
                    next_row = repo_df.iloc[index + 1].copy()
                    release_dir_next = os.path.join(args.data_dir, next_row['repository_name'], next_row['branch'])
                    next_row["date"] = str(next_row["date"])

                    logging.info(f'Parsing `{release_dir_current}` and `{release_dir_next}`')
                    repository1 = Repository(release_dir_current)
                    repository2 = Repository(release_dir_next)
                    logging.info(f'Comparing `{release_dir_current}` and `{release_dir_next}`')
                    comparator = RepositoryComparator(repository1, repository2)

                    del row['repository_name'], next_row['repository_name']
                    # initial release of the repository
                    if index == 0:
                        initial_data = comparator.get_initial_release_data()
                        for entry in initial_data:
                            fout.write(json.dumps({
                                **row.to_dict(),
                                "prev_branch": None,
                                **entry
                            }) + '\n')

                    for entry in comparator.files_data:
                        fout.write(json.dumps({
                            **next_row.to_dict(),
                            "prev_branch": row["branch"],
                            **entry
                        }) + '\n')
