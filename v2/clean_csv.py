import pandas as pd


if __name__ == "__main__":
    # remove duplicate releases for each repository

    input_file = 'download_data_raw.csv'
    output_file = 'download_data_cleaned.csv'

    df = pd.read_csv(input_file)

    df['date'] = pd.to_datetime(df['date'], utc=True)

    repositories = df['repository'].unique()

    filtered_dataframes = []
    for repo in repositories:
        repo_df = df[df['repository'] == repo]
        repo_df = repo_df.sort_values(by='date').drop_duplicates(subset='date', keep='last')
        filtered_dataframes.append(repo_df)

    final_df = pd.concat(filtered_dataframes, ignore_index=True)

    final_df.to_csv(output_file, index=False)
