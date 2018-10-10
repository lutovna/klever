#
# Copyright (c) 2018 ISP RAS (http://www.ispras.ru)
# Ivannikov Institute for System Programming of the Russian Academy of Sciences
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import glob

from core.utils import make_relative_path
from core.vog.abstractions.files_repr import File
from core.vog.abstractions.fragments_repr import Fragment


class Dependencies:

    def __init__(self, clade, source_paths):
        self.clade = clade
        self.source_paths = source_paths
        self.cmdg = self.clade.CommandGraph()
        self.srcg = self.clade.SourceGraph()
        self._files = dict()
        self._fragments = dict()
        self.__divide()
        self.__establish_dependencies()

    def create_fragment(self, name=None, files=None):
        fragment = Fragment(name)
        fragment.files.update(files)
        return fragment

    def remove_fragment(self, name):
        if name not in self._fragments:
            raise ValueError("Cannot remove already missing fragment {!r}".format(name))
        else:
            del self._fragments[name]

    def add_fragment(self, fragment):
        if fragment.name not in self._fragments:
            self._fragments[fragment.name] = fragment
        else:
            raise ValueError("Cannot create a duplicate fragment {!r}".format(fragment.name))

    @property
    def files(self):
        return self._files.values()

    @property
    def fragments(self):
        return self._fragments.values()

    @property
    def target_fragments(self):
        return {f for f in self.fragments if f.target}

    def find_files_for_expressions(self, expressions):
        # Copy to avoid modifying external data
        files = set()
        expressions = set(expressions)
        frags, matched = self.find_fragments_by_expressions(expressions)
        expressions.difference_update(matched)
        for fragment in frags:
            files.update(fragment.files)
        new_files, matched = self.find_files_by_expressions(expressions)
        files.update(new_files)

        return files

    def find_files_by_expressions(self, expressions):
        # First try globes
        suitable_files = set()
        matched = set()
        for path in self.source_paths:
            for expr in expressions:
                files = glob.glob(os.path.join(path, expr))
                files = {make_relative_path(self.source_paths, f) for f in files}
                for file in files.difference(suitable_files):
                    if file in self._files:
                        suitable_files.add(file)
                        matched.add(expr)

        # Final check
        files = set()
        rest = expressions.difference(matched)
        for file in self.files:
            if file.name in suitable_files:
                files.add(file)
            elif file.export_functions.intersection(rest):
                files.add(file)
                matched.update(file.export_functions.intersection(rest))

        return files, matched

    def find_fragments_by_expressions(self, expressions):
        frags = set()
        matched = set()
        for name in expressions:
            if name in self._fragments:
                frags.add(self._fragments[name])
                matched.add(name)
        return frags, matched

    def find_fragments_with_files(self, files):
        frags = set()
        files = {f if isinstance(f, str) else f.name for f in files}
        for frag in self.fragments:
            if {f.name for f in frag.files}.intersection(files):
                frags.add(frag)
        return frags

    def find_files_that_use_functions(self, functions):
        files = set()
        for file in self.files:
            if file.import_functions.intersection(functions):
                files.add(file)
        return files

    def create_fragment_from_ld(self, identifier, desc, name, cmdg, sep_nestd=False):
        ccs = cmdg.get_ccs_for_ld(identifier)

        files = set()
        for i, d in ccs:
            self.__check_cc(d)
            for in_file in d['in']:
                path = make_relative_path(self.source_paths, in_file)
                if not sep_nestd or (sep_nestd and os.path.dirname(path) == os.path.dirname(desc['out'][0])):
                    files.add(path)
        files, matched = self.find_files_by_expressions(files)
        rest = files.difference(matched)
        if rest:
            raise ValueError('Cannot find files: {}'.format(', '.join(rest)))
        fragment = self.create_fragment(name, files)
        return fragment

    def collect_dependencies(self, files, filter_func=lambda x: True, depth=None, maxfrags=None):
        layer = {files}
        deps = set()
        while layer and (depth is None or depth > 0) and (maxfrags is None or maxfrags > 0):
            new_layer = set()
            for file in layer:
                deps.add(file)
                if maxfrags:
                    maxfrags -= 1
                if maxfrags is not None and maxfrags == 0:
                    break

                for dep in file.successors:
                    if dep not in deps and dep not in new_layer and dep not in layer and filter_func(dep):
                        new_layer.add(dep)

            layer = new_layer
            if depth is not None:
                depth -= 1

        return deps

    def __divide(self):
        # Out file is used just to get an identifier for the fragment, thus it is Ok to use a random first. Later we
        # check that all fragments have unique names
        for identifier, desc in ((i, d) for i, d in self.cmdg.CCs if d.get('out') and len(d.get('out')) > 0):
            for f in desc.get('in'):
                name = make_relative_path(self.source_paths, f)
                if name not in self._files:
                    file = File(name)
                    file.cc = identifier
                    file.size = self.srcg.get_sizes([f]).values()[0]
                    self._files[name] = file

    def __check_cc(self, desc):
        if len(desc['in']) != 1:
            raise NotImplementedError('CC build commands with more than one input file are not supported')

        if len(desc['out']) != 1:
            raise NotImplementedError('CC build commands with more than one output file are not supported')

    def __establish_dependencies(self):
        cg = self.clade.CallGraph().graph
        fs = self.clade.FunctionsScopes().scope_to_funcs

        # Fulfil callgraph dependencies
        for path, functions in cg:
            if path in self._files:
                file_repr = self._files[path]
                for func, func_desc in functions:
                    tp = func_desc.get('type', 'static')
                    if tp != 'static':
                        file_repr.export_functions.add(func)

                    for calls_scope, called_functions in ((s, d) for s, d in func_desc.get('calls', dict()).items()
                                                          if s != path and s != 'unknown'):
                        if calls_scope in self._files:
                            caller = self._files[calls_scope]
                            caller.import_functions.add(func)
                            caller.add_successor(file_repr)

        # Add rest global functions
        for path, functions in fs:
            if path in self._files:
                file_repr = self._files[path]
                for func, func_desc in functions:
                    tp = func_desc.get('type', 'static')
                    if tp != 'static':
                        file_repr.export_functions.add(func)