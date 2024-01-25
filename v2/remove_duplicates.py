import re

import pandas as pd


def extract_version(branch_string):
    parts = branch_string.split('/')
    for part in parts:
        match = re.search(r'(v?\d+\.\d+(\.\d+)*)', part)
        if match:
            return part
    return None


if __name__ == "__main__":
    # remove duplicate releases for each repository

    input_file = 'download_data_raw.csv'
    output_file = 'download_data_cleaned.csv'

    df = pd.read_csv(input_file)
    df['version'] = df['branch'].apply(extract_version)

    repositories = df['repository'].unique()

    filtered_dataframes = []
    for repo in repositories:
        repo_df = df[df['repository'] == repo]
        duplicated_versions = repo_df[repo_df.duplicated(subset='version', keep=False)]
        if not duplicated_versions.empty:
            first_occurrence = duplicated_versions.drop_duplicates(subset='version', keep='first')
            filtered_dataframes.append(first_occurrence)

        non_duplicated_versions = repo_df[~repo_df.duplicated(subset='version', keep=False)]
        filtered_dataframes.append(non_duplicated_versions)

    final_df = pd.concat(filtered_dataframes, ignore_index=True)
    final_df.to_csv(output_file, index=False)
