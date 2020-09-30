from typing import Dict

from pyformlang.finite_automaton import EpsilonNFA, DeterministicFiniteAutomaton, State
from pyformlang.regular_expression import Regex

from wrappers import GraphWrapper, Edge


class RegexGraphWrapper(GraphWrapper):
    dfa: DeterministicFiniteAutomaton
    dfa_state_to_idx: Dict[State, int]

    def __init__(self, epsilon_nfa: EpsilonNFA):
        edges = []
        dfa = epsilon_nfa.to_deterministic()
        state_to_idx = dict([(state, index) for index, state in enumerate(dfa.states)])
        for state_from, transitions in epsilon_nfa.to_deterministic().to_dict().items():
            for label, state_to in transitions.items():
                edges.append(Edge(node_from=state_to_idx[state_from], node_to=state_to_idx[state_to], label=label))
        self.dfa = dfa
        self.dfa_state_to_idx = state_to_idx
        start_states = [self.dfa_state_to_idx[state] for state in self.dfa.start_states]
        final_states = [self.dfa_state_to_idx[state] for state in self.dfa.final_states]
        super().__init__(edges, start_states, final_states)

    @classmethod
    def from_regex(cls, regex: str, is_python_regex=True):
        if is_python_regex:
            pyformlang_regex = Regex.from_python_regex(regex)
        else:
            pyformlang_regex = Regex(regex)
        return RegexGraphWrapper(pyformlang_regex.to_epsilon_nfa().minimize())

    @classmethod
    def from_regex_file(cls, path_to_regex_file: str, is_python_regex=True):
        with open(path_to_regex_file, 'r') as file:
            line = file.readline()
        return cls.from_regex(line, is_python_regex)
