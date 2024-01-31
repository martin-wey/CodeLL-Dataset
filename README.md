# CodeLL - A Lifelong Learning Dataset for Source Code

Official repository associated with the MSR24 submission "CodeLL: A Lifelong Learning Dataset to Support the Co-Evolution of Data and Language Models of Code".

The first part of this README describes how to reproduce the data mining procedure of the paper. Then, it introduces how to perform the code change analysis.

--- 

**The repository is still under construction as we are preparing the release of a second version of the dataset.**

---

## Dataset

You can download the initial version of `CodeLL` using the following link: https://zenodo.org/records/10248423.

Each `.tar.gz` file contains a `.jsonl` file for a given repository. One line of a `.jsonl` file contains the following information:

```json
{     
  "repository": str, 
  "branch" : str, 
  "prev_branch" : str,
  "date": str, 
  "id": integer, 
  "imports": List[str],
  "methods": List[{
    "id": integer, 
    "class": str, 
    "name": str, 
    "params": List[str], 
    "content": str, 
    "function_calls": List[{
      "id": integer, 
      "expression": str,
      "start_offset": integer, 
      "end_offset": integer,
      "mapping": integer | "added" | "removed"
    },
    "mapping": integer | "added" | "removed"
  }],
  "mapping": integer | "added" | "removed"
}
```
It is possible to leverage our dataset for diverse downstream tasks and applications. We will release a script to generate training and test samples for selected downstream tasks in the future.



## Data mining procedure
You can replicate the data mining procedure with your own set of repositories available on Software Heritage by cloning this repository.

### 1. Get repositories releases

Use the `swh_miner.py` script to retrieve all the branches associated with the repositories.
We use a regex to only retrieve branches that contain a version (see `version_regex` variable in `swh_miner.py`).
The input of the script is a `.txt` file, where a line is a repository URL (e.g., https://pypi.org/project/gensim/).
```shell
python swh_miner.py --input_file ./dataset/v1/3k_python_dataset_filtered.txt
```
The script outputs a `download_data.csv` file in the input file directory. Each line of that `.csv` file contains information to download the branches content.

### 2. Manual filtering of the branches

We recommend to manually filter branches to avoid duplicates and mining non-release branches such as pull requests.
We will provide a script to automatically perform this filtering in the future.

### 3. Download the releases content
Use the `download_repos.py` script to download the releases content.
It takes as input the `download_data.csv` file, and an output directory.
```shell
python download_repos.py \
  --download_data_fp ./dataset/v1/download_data.csv \
  --output_dir ./dataset/v1/pypi/data
```
The script creates one folder per repository, and one subfolder for each release. 
Each release folder contains a `data.tar.gz` file containing the release content.

### 4. Data extraction
Use the `extract_data.sh` shell script to unzip the `data.tar.gz` files.
```shell
bash extract_data.sh ./dataset/v1/data ./dataset/v1/data
```
The first program argument is the path to the data, and the second one is the output directory.
The script only extracts `.py` and `requirements.txt` files for efficiency reasons. 

## Code change analysis
Use the `data_generator.py` script to perform the code change analysis and generate the `.jsonl` files:
```shell
python data_generator.py \
  --data_dir ./dataset/v1/data \
  --download_data_fp ./dataset/v1/download_data.csv \
  --output_dir ./dataset/v1/data
```
Currently, the code change analysis script compares two contiguous releases of a repository. 
However, it is possible to edit the `data_generator.py` script for comparing two specific releases, for instance. We will also release a more configurable `data_generator.py` in the future.