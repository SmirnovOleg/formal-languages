from typing import List

from pyformlang.cfg import Variable, Production, CFG
from pyformlang.finite_automaton import DeterministicFiniteAutomaton
from pyformlang.regular_expression import Regex
from pygraphblas import Matrix, types

from wrappers import GraphWrapper


class RFA:
    def __init__(self, graph, head_by_start_final_pair, eps_productions, start_symbol):
        self.graph = graph
        self.head_by_start_final_pair = head_by_start_final_pair
        self.eps_productions = eps_productions
        self.start_symbol = start_symbol

    @classmethod
    def from_cfg(cls, cfg: CFG):
        import wrappers.GraphWrapper
        rfa_graph = wrappers.GraphWrapper.empty()
        rfa_graph.matrix_size = sum([len(prod.body) + 1 for prod in cfg.productions])
        empty_matrix = Matrix.sparse(types.BOOL, rfa_graph.matrix_size, rfa_graph.matrix_size)
        head_by_start_final_pair, cnt = {}, 0
        for prod in cfg.productions:
            rfa_graph.start_states.add(cnt)
            head_by_start_final_pair[cnt, cnt + len(prod.body)] = prod.head.value
            for var in prod.body:
                matrix = rfa_graph.label_to_bool_matrix.setdefault(var.value, empty_matrix.dup())
                matrix[cnt, cnt + 1] = True
                cnt += 1
            rfa_graph.final_states.add(cnt)
            cnt += 1
        eps_productions = [prod for prod in cfg.productions if not prod.body]
        return cls(rfa_graph, head_by_start_final_pair, eps_productions, cfg.start_symbol)

    @classmethod
    def from_text(cls, text: List[str]):
        import wrappers.GraphWrapper
        rfa_graph = wrappers.GraphWrapper.empty()
        empty_matrix = Matrix.sparse(types.BOOL)
        head_by_start_final_pair = {}
        start_symbol = None
        eps_productions = []
        total_states_counter = 0
        for line in text:
            raw_head, raw_body = line.split(' ', 1)
            regex = Regex(raw_body)
            head = Variable(raw_head)
            if start_symbol is None:
                start_symbol = head
            if not raw_body:
                eps_productions.append(Production(head, []))

            dfa: DeterministicFiniteAutomaton = regex.to_epsilon_nfa().to_determenistic().minimize()
            transitions = dfa._transition_function._transitions
            num_by_state = {}
            for state in dfa.states:
                num_by_state[state] = total_states_counter
                total_states_counter += 1

            rfa_graph.start_states.add(num_by_state[dfa.start_state])
            for final_state in dfa.final_states:
                rfa_graph.final_states.add(num_by_state[final_state])
                head_by_start_final_pair[num_by_state[dfa.start_state], num_by_state[final_state]] = head.value

            for state_from in transitions:
                for edge_symb in transitions[state_from]:
                    state_to = transitions[state_from][edge_symb]
                    matrix = rfa_graph.label_to_bool_matrix.setdefault(edge_symb, empty_matrix.dup())
                    matrix[num_by_state[state_from], num_by_state[state_to]] = True

        rfa_graph.matrix_size = total_states_counter
        for matrix in rfa_graph.label_to_bool_matrix.values():
            matrix.resize(total_states_counter, total_states_counter)

        return cls(rfa_graph, head_by_start_final_pair, eps_productions, start_symbol)

    @classmethod
    def from_file(cls, path_to_file: str):
        with open(path_to_file, 'r') as file:
            return cls.from_text(file.readlines())
