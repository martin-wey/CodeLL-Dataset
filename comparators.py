import os

import Levenshtein

from parser import Repository, PythonFile, Method


class Comparator:
    @staticmethod
    def levenshtein_ratio_and_distance(str1, str2):
        return Levenshtein.ratio(str1, str2), Levenshtein.distance(str1, str2)

    @staticmethod
    def levenshtein_ratio(str1, str2):
        return Levenshtein.ratio(str1, str2)

    @staticmethod
    def get_line_count(content):
        return len(content.split("\n"))


class RepositoryComparator(Comparator):
    RATIO_FILE_NAMES_SIMILARITY = .75
    RATIO_FILE_COMMON_METHODS = .50

    def __init__(self, repo1: Repository, repo2: Repository):
        self.repo1 = repo1
        self.repo2 = repo2

        self.files_mapping = list(self.map_files())
        self.files_data = list(self.compare_files())

    def map_files(self):
        f1_parsed = set()
        f2_parsed = set()

        for file1 in self.repo1.files:
            if file1 in f1_parsed:
                continue
            # check for exact match between relative paths first
            for file2 in self.repo2.files:
                # calls __eq__ and compare relative paths
                if file1 == file2:
                    yield file1, file2
                    f1_parsed.add(file1)
                    f2_parsed.add(file2)
                    break

            # check for files with very similar names and a high ratio of shared methods
            if file1 not in f1_parsed:
                # make sure a file is not mapped twice
                repo2_files_filtered = [f2 for f2 in self.repo2.files if f2 not in f2_parsed]
                for file2 in repo2_files_filtered:
                    file1_name = os.path.split(str(file1))[-1]
                    file2_name = os.path.split(str(file2))[-1]

                    # check if file names are very similar
                    ratio_file_names = self.levenshtein_ratio(file1_name, file2_name)
                    if not ratio_file_names > self.RATIO_FILE_NAMES_SIMILARITY:
                        continue

                    # check the ratio of shared methods
                    file1_methods = [m.name for m in file1.methods]
                    file2_methods = [m.name for m in file2.methods]

                    if len(file1_methods) > 0 and len(file2_methods) > 0:
                        shortest_list = min(file1_methods, file2_methods, key=len)
                        longest_list = max(file1_methods, file2_methods, key=len)

                        common_method = set(shortest_list) & set(longest_list)
                        ratio_common_methods = len(common_method) / len(shortest_list)
                        if not ratio_common_methods > self.RATIO_FILE_COMMON_METHODS:
                            continue

                    yield file1, file2
                    f1_parsed.add(file1)
                    f2_parsed.add(file2)
                    break

            # file has probably been removed in the next release
            if file1 not in f1_parsed:
                yield file1, "removed"

        # new files in the new release of the repository
        new_files = [f2 for f2 in self.repo2.files if f2 not in f2_parsed]
        for f in new_files:
            yield f, "added"
            f2_parsed.add(f)

    def compare_files(self):
        for file1, file2 in self.files_mapping:
            if isinstance(file2, str):
                yield {
                    **file1.to_dict(),
                    "mapping": file2,
                    "imports": [i.content for i in file1.imports],
                    "methods": [
                        {
                            **m.to_dict(),
                            "function_calls": [fc.to_dict() for fc in m.function_calls],
                        }
                        for m in file1.methods
                    ]
                }
            else:
                comparator = PythonFileComparator(file1, file2)
                yield {
                    **file2.to_dict(),
                    "mapping": file2.to_dict()["id"],
                    "imports": [i.content for i in file2.imports],
                    "methods": comparator.methods_data
                }

    def get_initial_release_data(self):
        data = []
        for file in self.repo1.files:
            data.append({
                **file.to_dict(),
                "imports": [i.content for i in file.imports],
                "methods": [
                    {
                        **m.to_dict(),
                        "function_calls": [fc.to_dict() for fc in m.function_calls],
                    }
                    for m in file.methods
                ]
            })
        return data


class PythonFileComparator(Comparator):
    def __init__(self, file1: PythonFile, file2: PythonFile):
        self.file1 = file1
        self.file2 = file2

        self.methods_mapping = list(self.map_methods())
        self.methods_data = list(self.get_methods_data())

    def map_methods(self):
        m1_parsed = set()
        m2_parsed = set()

        for method1 in self.file1.methods:
            if method1 in m1_parsed:
                continue
            # check for exact match (class_name, name and params) between both methods
            for method2 in self.file2.methods:
                if method2 in m2_parsed:
                    continue
                if method1 == method2:
                    yield method1, method2
                    m1_parsed.add(method1)
                    m2_parsed.add(method2)
                    break

            # check for partial match (class_name, name) --> handle the case where params change
            if method1 not in m1_parsed:
                file2_methods_filtered = [m2 for m2 in self.file2.methods if m2 not in m2_parsed]
                for method2 in file2_methods_filtered:
                    if method1.partial_eq(method2):
                        yield method1, method2
                        break

            # method removed in the new release
            if method1 not in m1_parsed:
                yield method1, "removed"

        # new methods in the new release of the repository
        new_methods = [m2 for m2 in self.file2.methods if m2 not in m2_parsed]
        for m in new_methods:
            yield m, "added"
            m2_parsed.add(m)

    def get_methods_data(self):
        for m1, m2 in self.methods_mapping:
            if isinstance(m2, str):
                yield {
                    **m1.to_dict(),
                    "mapping": m2,
                    "function_calls": [
                        {
                            **fc.to_dict(),
                        }
                        for fc in m1.function_calls
                    ]
                }
            else:
                comparator = MethodComparator(m1, m2)
                ratio, distance = self.levenshtein_ratio_and_distance(m1.content, m2.content)
                yield {
                    **m2.to_dict(),
                    "mapping": m1.to_dict()["id"],
                    "function_calls": comparator.fc_data,
                    "statistics": {
                        "ratio": ratio,
                        "dist": distance
                    }
                }


class MethodComparator(Comparator):
    def __init__(self, method1: Method, method2: Method):
        self.method1 = method1
        self.method2 = method2

        self.fc_mapping = list(self.map_function_calls())
        self.fc_data = list(self.get_function_calls_data())

    def map_function_calls(self):
        self.method1.sort_fc_calls_by_start_offset()
        self.method2.sort_fc_calls_by_start_offset()
        fcs1_parsed = set()
        fcs2_parsed = set()

        for i, fc1 in enumerate(self.method1.function_calls):
            if (i, fc1) in fcs1_parsed:
                continue
            for j, fc2 in enumerate(self.method2.function_calls):
                if (j, fc2) in fcs2_parsed:
                    continue

                # fcs are identical and have the same start/end offsets -> most-likely no change.
                if fc1 == fc2:
                    yield fc1, fc2
                    fcs1_parsed.add((i, fc1))
                    fcs2_parsed.add((j, fc2))
                    break

                # fcs are similar (e.g., np.mean == np.mean), but different offsets.
                elif fc1.context == fc2.context and fc1.name == fc2.name:
                    yield fc1, fc2
                    fcs1_parsed.add((i, fc1))
                    fcs2_parsed.add((j, fc2))
                    break

            if (i, fc1) not in fcs1_parsed:
                yield fc1, "removed"
                fcs1_parsed.add((i, fc1))

        for j, fc in enumerate(self.method2.function_calls):
            if (j, fc) not in fcs2_parsed:
                yield fc, "added"

    def get_function_calls_data(self):
        for fc1, fc2 in self.fc_mapping:
            if isinstance(fc2, str):
                yield {
                    **fc1.to_dict(),
                    "mapping": fc2
                }
            else:
                ratio, distance = self.levenshtein_ratio_and_distance(fc1.expression, fc2.expression)
                yield {
                    **fc2.to_dict(),
                    "mapping": fc1.to_dict()["id"],
                    "statistics": {
                        "ratio": ratio,
                        "dist": distance
                    }
                }
