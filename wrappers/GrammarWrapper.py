from typing import List, Dict

from pyformlang.cfg import Variable, Terminal, CFG, Production
from pyformlang.finite_automaton import State
from pyformlang.regular_expression import Regex


class GrammarWrapper:
    __var_state_counter = 0

    def __init__(self, cfg: CFG):
        self.cfg = cfg
        self.generate_epsilon = cfg.generate_epsilon()
        self.cnf = cfg.to_normal_form()
        self.wcnf = self.get_weak_cnf()

    @classmethod
    def from_text(cls, text: List[str], use_python_regexes_if_necessary=False):
        vars, terms, prods = set(), set(), set()
        start_var = None
        for line in text:
            if not line.strip():
                continue
            raw_head, *raw_body = line.strip().split(' ', 1)
            if raw_body and any([spec in raw_body[0] for spec in ['|', '.', '?', '+', '-']]):
                if '-' in raw_body[0] and use_python_regexes_if_necessary:
                    regex = Regex.from_python_regex(raw_body[0])
                else:
                    regex = Regex(raw_body[0])
                head = Variable(raw_head)
                if start_var is None:
                    start_var = head
                cur_cfg = cls._create_cfg_from_regex(head, regex)
                vars.update(cur_cfg.variables)
                terms.update(cur_cfg.terminals)
                prods.update(cur_cfg.productions)
            else:
                raw_body = raw_body[0].split(' ') if raw_body else ''
                if start_var is None:
                    start_var = Variable(raw_head)
                head = Variable(raw_head)
                vars.add(head)
                body = []
                for element in raw_body:
                    if element == 'eps':
                        continue
                    elif any(letter.isupper() for letter in element):
                        var = Variable(element)
                        vars.add(var)
                        body.append(var)
                    else:
                        term = Terminal(element)
                        terms.add(term)
                        body.append(term)
                prods.add(Production(head, body))
        cfg = CFG(vars, terms, start_var, prods)
        return cls(cfg)

    @classmethod
    def from_file(cls, path_to_file: str, use_python_regexes_if_necessary=False):
        with open(path_to_file, 'r') as file:
            return cls.from_text(file.readlines(), use_python_regexes_if_necessary)

    @classmethod
    def _create_cfg_from_regex(cls, head: Variable, regex: Regex) -> CFG:
        dfa = regex.to_epsilon_nfa().to_deterministic().minimize()
        transitions = dfa._transition_function._transitions
        state_to_var: Dict[State, Variable] = {}
        productions, terms, vars = set(), set(), set()
        for state in dfa.states:
            state_to_var[state] = Variable(f'{state}:{cls.__var_state_counter}')
            cls.__var_state_counter += 1
        vars.update(state_to_var.values())
        for start_state in dfa.start_states:
            productions.add(Production(head, [state_to_var[start_state]]))
        for state_from in transitions:
            for edge_symb in transitions[state_from]:
                state_to = transitions[state_from][edge_symb]
                current_prod_head = state_to_var[state_from]
                current_prod_body = []
                if edge_symb.value.isupper():
                    var = Variable(edge_symb.value)
                    vars.add(var)
                    current_prod_body.append(var)
                else:
                    term = Terminal(edge_symb.value)
                    terms.add(term)
                    current_prod_body.append(term)
                current_prod_body.append(state_to_var[state_to])
                productions.add(Production(current_prod_head, current_prod_body))
                if state_to in dfa.final_states:
                    productions.add(Production(state_to_var[state_to], []))
        if not productions:
            return CFG(vars, terms, head, {Production(head, [])})
        return CFG(vars, terms, head, productions)

    def get_weak_cnf(self) -> CFG:
        wcnf = self.cnf
        if self.generate_epsilon:
            new_start_symbol = Variable("S'")
            new_variables = set(wcnf.variables)
            new_variables.add(new_start_symbol)
            new_productions = set(wcnf.productions)
            new_productions.add(Production(new_start_symbol, [wcnf.start_symbol]))
            new_productions.add(Production(new_start_symbol, []))
            return CFG(new_variables, wcnf.terminals, new_start_symbol, new_productions)
        return wcnf

    def accepts(self, word) -> bool:
        size = len(word)
        if size == 0:
            return self.cfg.generate_epsilon()
        cnf = self.cfg.to_normal_form()
        inference_matrix = [[set() for _ in range(size)] for _ in range(size)]
        for i in range(size):
            term = Terminal(word[i])
            for prod in cnf.productions:
                if len(prod.body) == 1 and prod.body[0] == term:
                    inference_matrix[i][i].add(prod.head)
        for length in range(1, size):
            for pos in range(size):
                if pos + length >= size:
                    break
                for split in range(length):
                    first_part = inference_matrix[pos][pos + split]
                    second_part = inference_matrix[pos + split + 1][pos + length]
                    for prod in cnf.productions:
                        if len(prod.body) == 2:
                            if prod.body[0] in first_part and prod.body[1] in second_part:
                                inference_matrix[pos][pos + length].add(prod.head)
        return cnf.start_symbol in inference_matrix[0][size - 1]
