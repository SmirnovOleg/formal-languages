from pyformlang.cfg import Variable, Terminal, CFG, Production


class GrammarWrapper:
    cfg: CFG

    def __init__(self, cfg: CFG):
        self.cfg = cfg

    @classmethod
    def from_file(cls, path_to_file: str):
        vars, terms, prods = set(), set(), set()
        start_var = None
        with open(path_to_file, 'r') as file:
            for line in file.readlines():
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

    def contains_using_CYK(self, word: str):
        self.cfg.to_normal_form()
        size = len(word)
        if size == 0:
            raise NotImplementedError('Epsilons are not currently supported')
        inference_matrix = [[set() for _ in range(size)] for _ in range(size)]
        for i in range(size):
            term = Terminal(word[i])
            for prod in self.cfg.productions:
                if len(prod.body) == 1 and prod.body[0] == term:
                    inference_matrix[i][i].add(prod.head)
        for length in range(1, size):
            for pos in range(size):
                if pos + length >= size:
                    break
                for split in range(length):
                    first_part = inference_matrix[pos][pos + split]
                    second_part = inference_matrix[pos + split + 1][pos + length]
                    for prod in self.cfg.productions:
                        if len(prod.body) == 2:
                            if prod.body[0] in first_part and prod.body[1] in second_part:
                                inference_matrix[pos][pos + length].add(prod.head)
        return self.cfg.start_symbol in inference_matrix[0][size - 1]


if __name__ == '__main__':
    wrapper = GrammarWrapper.from_file('grammar.txt')
    print(wrapper.contains_using_CYK(''))
