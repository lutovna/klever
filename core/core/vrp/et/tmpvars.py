#
# Copyright (c) 2019 ISP RAS (http://www.ispras.ru)
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

import re


def generic_simplifications(logger, trace):
    logger.info('Simplify error trace')
    _remove_switch_cases(logger, trace)
    # _merge_func_entry_and_exit(logger, trace)
    # _remove_tmp_vars(logger, trace)
    trace.sanity_checks()


def _remove_tmp_vars(logger, error_trace):
    # Get rid of temporary variables. Replace:
    #   ... tmp...;
    #   ...
    #   tmp... = func(...);
    #   [... tmp... ...;]
    # with (removing first and last statements if so):
    #   ...
    #   ... func(...) ...;
    removed_tmp_vars_num = __remove_tmp_vars(error_trace, next(error_trace.trace_iterator()))[0]

    if removed_tmp_vars_num:
        logger.debug('{0} temporary variables were removed'.format(removed_tmp_vars_num))


def __remove_tmp_vars(error_trace, edge):
    removed_tmp_vars_num = 0

    # Remember current function. All temporary variables defined in a given function can be used just in it.
    # The only function for which we can't do this is main (entry point) since we don't enter it explicitly but it
    # never returns due to some errors happen early so it doesn't matter.
    if 'enter' in edge:
        func_id = edge['enter']
        return_edge = error_trace.get_func_return_edge(edge)
        # Move forward to function declarations or/and statements.
        edge = error_trace.next_edge(edge)
    else:
        return_edge = None

    # Scan variable declarations to find temporary variable names and corresponding edge ids.
    tmp_var_names = dict()
    edges_map = dict()
    for edge in error_trace.trace_iterator(begin=edge):
        # Declarations are considered to finish when entering/returning from function, some condition is checked or some
        # assigment is performed. Unfortunately we consider calls to functions without bodies that follow declarations
        # as declarations.
        if 'return' in edge or 'enter' in edge or 'condition' in edge or '=' in edge['source']:
            break

        m = re.search(r'(tmp\w*);$', edge['source'])
        if m:
            edges_map[id(edge)] = edge
            tmp_var_names[m.group(1)] = id(edge)

    # Remember what temporary varibles aren't used after all. Temporary variables that are really required will be
    # remained as is.
    unused_tmp_var_decl_ids = set(list(tmp_var_names.values()))

    # Scan statements to find function calls which results are stored into temporary variables.
    error_trace_iterator = error_trace.trace_iterator(begin=edge)
    for edge in error_trace_iterator:
        # Reach end of current function.
        if edge is return_edge:
            break

        # Remember current edge that can represent function call. We can't check this by presence of attribute "enter"
        # since functions can be without bodies and thus without enter-return edges.
        func_call_edge = edge

        # Recursively get rid of temporary variables inside called function if there are some edges belonging to that
        # function.
        if 'enter' in edge and error_trace.next_edge(func_call_edge):
            removed_tmp_vars_num_tmp, next_edge = __remove_tmp_vars(error_trace, func_call_edge)
            removed_tmp_vars_num += removed_tmp_vars_num_tmp

            # Skip all edges belonging to called function.
            while True:
                edge = next(error_trace_iterator)
                if edge is next_edge:
                    break

        # Result of function call is stored into temporary variable.
        m = re.search(r'^(tmp\w*)\s+=\s+(.+);$', func_call_edge['source'])

        if not m:
            continue

        tmp_var_name = m.group(1)
        func_call = m.group(2)

        # Do not proceed if found temporary variable wasn't declared. Actually it will be very strange if this will
        # happen
        if tmp_var_name not in tmp_var_names:
            continue

        tmp_var_decl_id = tmp_var_names[tmp_var_name]

        # Try to find temorary variable usages on edges following corresponding function calls.
        tmp_var_use_edge = error_trace.next_edge(edge)

        # There is no usage of temporary variable but we still can remove its declaration and assignment.
        if not tmp_var_use_edge:
            func_call_edge['source'] = func_call + ';'
            break

        # Skip simplification of the following sequence:
        #   ... tmp...;
        #   ...
        #   tmp... = func(...);
        #   ... gunc(... tmp... ...);
        # since it requires two entered functions from one edge.
        if 'enter' in tmp_var_use_edge:
            # Do not assume that each temporary variable is used only once. This isn't the case when they are used
            # within cycles. That's why do not require temporary variable to be in list of temporary variables to be
            # removed - it can be withdrawn from this list on previous cycle iteration.
            if tmp_var_decl_id in unused_tmp_var_decl_ids:
                unused_tmp_var_decl_ids.remove(tmp_var_decl_id)
        else:
            m = re.search(r'^(.*){0}(.*)$'.format(tmp_var_name), tmp_var_use_edge['source'])

            # Do not proceed if pattern wasn't matched.
            if not m:
                continue

            func_call_edge['source'] = m.group(1) + func_call + m.group(2)

            # Move vital attributes from edge to be removed. If this edge represents warning it can not be removed
            # without this.
            for attr in ('condition', 'return', 'note', 'warn'):
                if attr in tmp_var_use_edge:
                    func_call_edge[attr] = tmp_var_use_edge.pop(attr)

            # Edge to be removed is return edge from current function.
            is_reach_cur_func_end = True if tmp_var_use_edge is return_edge else False

            # Remove edge corresponding to temporary variable usage.
            error_trace.remove_edge_and_target_node(tmp_var_use_edge)

            removed_tmp_vars_num += 1

            if is_reach_cur_func_end:
                break

    # Remove all temporary variable declarations in any case.
    for tmp_var_decl_id in reversed(list(unused_tmp_var_decl_ids)):
        error_trace.remove_edge_and_target_node(edges_map[tmp_var_decl_id])

    return removed_tmp_vars_num, edge


def _remove_switch_cases(logger, error_trace):
    # Get rid of redundant switch cases. Replace:
    #   assume(x != A)
    #   assume(x != B)
    #   ...
    #   assume(x == Z)
    # with:
    #   assume(x == Z)
    removed_switch_cases_num = 0
    for edge in error_trace.trace_iterator():
        # Begin to match pattern just for edges that represent conditions.
        if 'condition' not in edge:
            continue

        # Get all continues conditions.
        cond_edges = []
        for cond_edge in error_trace.trace_iterator(begin=edge):
            if 'condition' not in cond_edge:
                break
            cond_edges.append(cond_edge)

        # Do not proceed if there is not continues conditions.
        if len(cond_edges) == 1:
            continue

        x = None
        start_idx = 0
        cond_edges_to_remove = []
        for idx, cond_edge in enumerate(cond_edges):
            m = re.search(r'^(.+) ([=!]=)', cond_edge['source'])

            # Start from scratch if meet unexpected format of condition.
            if not m:
                x = None
                continue

            # Do not proceed until first condition matches pattern.
            if x is None and m.group(2) != '!=':
                continue

            # Begin to collect conditions.
            if x is None:
                start_idx = idx
                x = m.group(1)
                continue
            # Start from scratch if first expression condition differs.
            elif x != m.group(1):
                x = None
                continue

            # Finish to collect conditions. Pattern matches.
            if x is not None and m.group(2) == '==':
                cond_edges_to_remove.extend(cond_edges[start_idx:idx])
                x = None
                continue

        for cond_edge in reversed(cond_edges_to_remove):
            error_trace.remove_edge_and_target_node(cond_edge)
            removed_switch_cases_num += 1

    if removed_switch_cases_num:
        logger.debug('{0} switch cases were removed'.format(removed_switch_cases_num))


def _merge_func_entry_and_exit(logger, error_trace):
    # For each function call with return there is an edge corresponding to function entry and an edge
    # corresponding to function exit. Both edges are located at a function call. The second edge can contain an
    # assigment of result to some variable.
    # This is good for analysis, but this is redundant for visualization. Let's merge these edges together.
    edges_to_remove = []
    for edge in error_trace.trace_iterator():
        if 'enter' in edge:
            return_edge = error_trace.get_func_return_edge(edge)
            if return_edge:
                exit_edge = error_trace.next_edge(return_edge)
                edges_to_remove.insert(0, exit_edge)
                edge['source'] = exit_edge['source']

    for edge_to_remove in edges_to_remove:
        error_trace.remove_edge_and_target_node(edge_to_remove)
