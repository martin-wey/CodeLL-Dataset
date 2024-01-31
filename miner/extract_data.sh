#!/bin/bash

# 1. bash extract_data.sh /Tmp/codell_v2/ /Tmp/codell_v2/ data.tar.gz 0   -> extract using tar
# 2. bash extract_data.sh /Tmp/codell_v2/ /Tmp/codell_v2/ data.tar.gz 1   -> extract using gzip
# 3. bash extract_data.sh /Tmp/codell_v2/ /Tmp/codell_v2/ data.tar 0      -> extract using tar

data_dir=$1
output_dir=$2
tar_file_name=$3
use_gzip=$4

export use_gzip

extract_tar() {
    file="$1"

    extract_dir=$(dirname "$file")

    if [ -z "$(find "$extract_dir" \( -name '*.py' -o -name 'requirements*.txt' \))" ]; then
      if [ "$use_gzip" = "1" ]; then
        echo "Extracting $file using gzip"
        gzip -d "$file"
      else
        echo "Extracting $file to $extract_dir"

        # only extract python files and requirements
        tar -xzf "$file" -C "$extract_dir" --wildcards --no-anchored '*.py' 'requirements*.txt' --strip-components 1

        echo "Done $file"
      fi
    fi
}

export -f extract_tar

# move data to output_dir
if [ "$data_dir" != "$output_dir" ]; then
  find "$data_dir" -mindepth 0 -maxdepth 0 -type d -print0 | xargs -0 -I {} -P 16 rsync -a --progress {}/ "$output_dir"
fi

# search for all `data.tar.gz` files and extract their content
find "$output_dir" -mindepth 1 -type f -name "$tar_file_name" -print0 | xargs -0 -n 1 -P 16 -I {} bash -c 'extract_tar "$@"' _ {}
