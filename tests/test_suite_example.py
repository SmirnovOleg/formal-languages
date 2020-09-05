from itertools import chain

from pygraphblas import Matrix


def create_matrix_from_array(array):
    zipped = [[(i, j, v) for j, v in enumerate(row)] for i, row in enumerate(array)]
    return Matrix.from_lists(*zip(*(chain.from_iterable(zipped))))


def test_matrix_product():
    a = create_matrix_from_array([[1, 1], [1, 1]])
    b = create_matrix_from_array([[2, 2], [2, 2]])
    matrix_actual = a @ b
    matrix_expected = create_matrix_from_array([[4, 4], [4, 4]])
    assert matrix_expected.iseq(matrix_actual)
