sed -i '/,,,,/d' download_data_raw.csv
sed -i '/\/dependabot\//d' download_data_raw.csv
sed -i '/\/pull\//d' download_data_raw.csv
python remove_duplicates.py