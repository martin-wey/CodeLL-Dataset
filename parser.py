import ast
import glob
import multiprocessing
import os
import sys
from pathlib import Path

from packaging.requirements import InvalidRequirement
from pkg_resources import parse_requirements
from tqdm import tqdm

tqdm_kwargs = {
    'bar_format': '{l_bar}{bar:100}{r_bar}{bar:-10b}',
    'file': sys.stdout
}


class Repository:
    def __init__(self, path, base_path='data', num_workers=16):
        self.path = path
        self.relative_path = os.path.relpath(self.path, base_path)
        self.num_workers = num_workers
        self.files = []
        self.requirements = []
        self.init_python_files()
        # self.init_requirements()

    def init_python_files(self):
        python_files = [Path(file) for file in glob.iglob(os.path.join(self.path, '**/*.py'), recursive=True)]

        if self.num_workers > 0:
            with multiprocessing.Pool(16) as pool:
                self.files = list(tqdm(pool.imap(self.parse_python_file, python_files),
                                       total=len(python_files),
                                       desc='Parsing .py files',
                                       **tqdm_kwargs))
        else:
            self.files = [self.parse_python_file(file)
                          for file in tqdm(python_files, desc='Parsing .py files', **tqdm_kwargs)]

    def parse_python_file(self, file):
        return PythonFile(file, self)

    def init_requirements(self):
        # @todo: fix parsing of:
        #   e.g., git+https://github.com/ShangtongZhang/dm_control2gym.git@scalar_fix
        requirements_file_path = os.path.join(self.path, 'requirements.txt')

        if os.path.exists(requirements_file_path):
            self.requirements = RequirementsFile(requirements_file_path)

    def get_all_files_paths(self):
        return [str(file) for file in self.files]

    def __str__(self):
        return str(self.relative_path)


class PythonFile:
    def __init__(self, path, repository):
        self.path = path
        self.relative_path = os.path.relpath(self.path, repository.path)
        self.repository = repository
        self.methods = []
        self.imports = []
        self.content = self.read_content()
        if self.content:
            try:
                self.parse_content()
            except SyntaxError:
                del self

    def read_content(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as file:
                return file.read()
        except:
            del self

    def parse_content(self):
        try:
            tree = ast.parse(self.content)

            # retrieve standalone functions
            standalone_functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
            for f in standalone_functions:
                name, content, params = self.get_function_node_info(f)
                function = Method(file=self, class_name=None, name=name, params=params, content=content)
                self.methods.append(function)

            # retrieve class methods
            classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
            for cls in classes:
                methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)]
                for m in methods:
                    name, content, params = self.get_function_node_info(m)
                    function = Method(file=self, class_name=cls.name, name=name, params=params, content=content)
                    self.methods.append(function)

            # retrieve imports
            imports = [n for n in tree.body if isinstance(n, ast.Import)]
            for i in imports:
                for alias in i.names:
                    import_name, import_alias, full_import_name = self.get_import_alias_info(alias)
                    import_obj = Import(import_name, import_alias, full_import_name)
                    self.imports.append(import_obj)

            # retrieve imports from
            imports_from = [n for n in tree.body if isinstance(n, ast.ImportFrom)]
            for i in imports_from:
                module = i.module
                for alias in i.names:
                    import_name, import_alias, full_import_name = self.get_import_alias_info(alias, module, True)
                    import_obj = Import(import_name, import_alias, full_import_name)
                    self.imports.append(import_obj)
        except SyntaxError:
            raise SyntaxError('Invalid Python syntax')

    def get_function_node_info(self, node):
        name = node.name
        content = ast.unparse(node)
        params = []
        for param in node.args.args:
            param_name = param.arg
            params.append(param_name)
        return name, content, params

    def get_import_alias_info(self, alias, module=None, import_from=False):
        import_name = alias.name
        import_alias = alias.asname
        if import_alias is not None:
            if import_from:
                full_import_name = f'from {module} import {import_name} as {import_alias}'
            else:
                full_import_name = f'import {import_name} as {import_alias}'
        else:
            if import_from:
                full_import_name = f'from {module} import {import_name}'
            else:
                full_import_name = f'import {import_name}'
        return import_name, import_alias, full_import_name

    def to_dict(self):
        return {
            'id': str(self.__hash__()),
            'path': self.relative_path
        }

    def __str__(self):
        return str(self.relative_path)

    def __eq__(self, other):
        return self.relative_path == other.relative_path

    def __hash__(self):
        return hash(self.relative_path)


class RequirementsFile:
    def __init__(self, path):
        self.path = path
        self.requirements = list(self.parse_requirements())

    def parse_requirements(self):
        try:
            with open(self.path, "r") as file:
                requirements = parse_requirements(file)
                for req in requirements:
                    yield {req.name: [str(spec) for spec in req.specs]}
        except InvalidRequirement as e:
            print(f"Error parsing requirement: {e}")


class Method:
    def __init__(self, file, class_name, name, params, content=None):
        self.file = file
        self.class_name = class_name
        self.name = name
        self.params = params
        self.content = content
        self.locs = []
        self.locs_no_comments = []
        self.retrieve_lines()
        self.content_no_comments = '\n'.join([loc.get_line_content() for loc in self.locs_no_comments])
        self.function_calls = []
        self.retrieve_function_calls()

    def retrieve_lines(self):
        if self.content is not None:
            lines = self.content.split('\n')
            inside_multi_line_comment = False

            current_line_number = 0
            for i, line in enumerate(lines):
                current_line_number += 1
                # ignore comments, but still take them into account in the line counter.
                if not inside_multi_line_comment:
                    # check for the start of a multi-line comment
                    if "'''" in line or '"""' in line:
                        inside_multi_line_comment = True

                    # exclude single-line comments and empty lines
                    elif line.strip() and not line.strip().startswith('#'):
                        loc = LOC(i, line)
                        self.locs_no_comments.append(loc)
                else:
                    # check for the end of a multi-line comment
                    if "'''" in line or '"""' in line:
                        inside_multi_line_comment = False
                loc = LOC(i, line)
                self.locs.append(loc)

    def retrieve_function_calls(self):
        tree = ast.parse(self.content)
        for node in ast.walk(tree):
            self.process_call_node(node)

    def process_call_node(self, node):
        if isinstance(node, ast.Call):
            context = self.get_call_context(node)
            function_name = self.get_call_name(node)

            fc_name = function_name
            if context is not None:
                fc_name = context
                context = function_name

            if fc_name:
                function_call_expr = ast.unparse(node)
                start_line = node.lineno - 1
                start_offset = self.get_start_char_index(self.content, start_line, node)
                end_offset = start_offset + len(function_call_expr)
                fc = FunctionCall(fc_name, context, function_call_expr, start_offset, end_offset, self.locs[start_line])
                if fc not in self.function_calls:
                    self.function_calls.append(fc)
        for child_node in ast.iter_child_nodes(node):
            self.process_call_node(child_node)

    @staticmethod
    def get_call_name(call_node):
        # Get the name of the function being called
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute) and isinstance(call_node.func.value, ast.Name):
            return call_node.func.value.id
        else:
            return None

    @staticmethod
    def get_call_context(call_node):
        # Get the context (word preceding the dot) of the function call
        if isinstance(call_node.func, ast.Attribute) and isinstance(call_node.func.value, ast.Name):
            return call_node.func.attr
        else:
            return None

    @staticmethod
    def get_start_char_index(code, start_line, node):
        lines = code.split('\n')
        # + 1 accounts for the \n tokens that is removed when splitting the code
        start_char = sum(len(line) + 1 for line in lines[:start_line]) + node.col_offset
        return start_char

    def sort_fc_calls_by_start_offset(self):
        self.function_calls.sort(key=lambda fc: fc.start_offset)

    def to_dict(self):
        return {
            'id': str(self.__hash__()),
            'class': self.class_name,
            'name': self.name,
            'params': self.params,
            'content': self.content
        }

    def __str__(self):
        return self.content

    def __hash__(self):
        return hash((self.class_name, self.name, ' '.join(self.params)))

    def __len__(self):
        return len(self.all_locs)

    def __eq__(self, other):
        return self.class_name == other.class_name and self.name == other.name and self.params == other.params

    def partial_eq(self, other):
        return self.class_name == other.class_name and self.name == other.name


class Import:
    def __init__(self, name, alias=None, content=None):
        self.name = name
        self.alias = alias
        self.content = content

    def to_dict(self):
        return self.__dict__

    def __eq__(self, other):
        return (self.name == other.name and self.alias == other.alias) or self.content == other.content

    def __hash__(self):
        return hash((self.name, self.alias, self.content))

    def __str__(self):
        return f'{self.alias} - {self.name} - {self.content}'


class LOC:
    def __init__(self, line_number, content):
        self.line_number = line_number
        self.content = content.strip()

    def get_line_content(self):
        return self.content

    def __str__(self):
        return f'Line {self.line_number}: {self.content}'

    def __eq__(self, other):
        return self.content == other.content


class FunctionCall:
    def __init__(self, fc_name, context, fc_expression, start_offset, end_offset, line):
        self.name = fc_name
        self.context = context
        self.expression = fc_expression
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.line = line

    def to_dict(self):
        return {
            'id': str(self.__hash__()),
            'name': self.name,
            'context': self.context,
            'expression': self.expression,
            'start_offset': self.start_offset,
            'end_offset': self.end_offset,
            'lineno': self.line.line_number
        }

    def __str__(self):
        return f'{self.context} - {self.name} - {self.expression} (start: {self.start_offset}, end: {self.end_offset})'

    def __hash__(self):
        return hash((self.expression, self.start_offset, self.end_offset))

    def __eq__(self, other):
        return (self.expression == other.expression
                and self.start_offset == other.start_offset
                and self.end_offset == other.end_offset)
