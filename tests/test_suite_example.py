from itertools import chain

from pyformlang.finite_automaton import State, Symbol, EpsilonNFA
from pyformlang.pda import State, Symbol
from pygraphblas import Matrix


def create_matrix_from_array(array):
    zipped = [[(i, j, v) for j, v in enumerate(row)] for i, row in enumerate(array)]
    return Matrix.from_lists(*zip(*(chain.from_iterable(zipped))))


def test_matrix_product():
    A = create_matrix_from_array([[1, 1], [1, 1]])
    B = create_matrix_from_array([[2, 2], [2, 2]])
    actual_matrix_product = A @ B
    expected_matrix = create_matrix_from_array([[4, 4], [4, 4]])
    assert expected_matrix.iseq(actual_matrix_product)


def test_pda_intersection():
    q0 = State("q0")
    q1 = State("q1")
    q2 = State("q2")
    q3 = State("q3")

    a = Symbol("a")
    b = Symbol("b")
    c = Symbol("c")

    epsilon_nfa_1 = EpsilonNFA(states={q0, q1, q2},
                               input_symbols={a, b},
                               start_state={q0},
                               final_states={q1, q2})
    epsilon_nfa_1.add_transition(q0, a, q1)
    epsilon_nfa_1.add_transition(q1, b, q2)

    epsilon_nfa_2 = EpsilonNFA(states={q0, q1, q3},
                               input_symbols={a, c},
                               start_state={q0},
                               final_states={q1, q3})
    epsilon_nfa_2.add_transition(q0, a, q1)
    epsilon_nfa_2.add_transition(q1, c, q3)

    expected_epsilon_nfa = EpsilonNFA(states={q0, q1},
                                      input_symbols={a},
                                      start_state={q0},
                                      final_states={q1})
    expected_epsilon_nfa.add_transition(q0, a, q1)

    actual_intersection = epsilon_nfa_1.get_intersection(epsilon_nfa_2)
    assert expected_epsilon_nfa.is_equivalent_to(actual_intersection)
