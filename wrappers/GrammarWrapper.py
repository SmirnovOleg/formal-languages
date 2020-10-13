from typing import List

from pyformlang.cfg import Variable, Terminal, CFG, Production
from pygraphblas import types, Matrix

import wrappers


class GrammarWrapper:

    def __init__(self, cfg: CFG, to_normal_form=False):
        if to_normal_form:
            self.cfg = cfg.to_normal_form()
        else:
            self.cfg = cfg
        rfa, production_by_vertices = self.__calculate_rfa()
        self.rfa = rfa
        self.production_by_vertices = production_by_vertices

    @classmethod
    def from_text(cls, text: List[str]):
        vars, terms, prods = set(), set(), set()
        start_var = None
        for line in text:
            raw_head, *raw_body = line.split()
            if start_var is None:
                start_var = Variable(raw_head)
            head = Variable(raw_head)
            vars.add(head)
            body = []
            for element in raw_body:
                if element.islower():
                    term = Terminal(element)
                    terms.add(term)
                    body.append(term)
                else:
                    var = Variable(element)
                    vars.add(var)
                    body.append(var)
            prods.add(Production(head, body))
        cfg = CFG(vars, terms, start_var, prods)
        return cls(cfg)

    @classmethod
    def from_file(cls, path_to_file: str):
        with open(path_to_file, 'r') as file:
            return cls.from_text(file.readlines())

    def __calculate_rfa(self):
        rfa = wrappers.GraphWrapper.empty()
        rfa.matrix_size = sum([len(prod.body) + 1 for prod in self.cfg.productions])
        empty_matrix = Matrix.sparse(types.BOOL, rfa.matrix_size, rfa.matrix_size)
        production_by_vertices, cnt = {}, 0
        for prod in self.cfg.productions:
            rfa.start_states.add(cnt)
            production_by_vertices[cnt, cnt + len(prod.body)] = prod
            for var in prod.body:
                matrix = rfa.label_to_bool_matrix.setdefault(var.value, empty_matrix.dup())
                matrix[cnt, cnt + 1] = True
                cnt += 1
            rfa.final_states.add(cnt)
            cnt += 1
        return rfa, production_by_vertices

    def accepts(self, word: str) -> bool:
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
