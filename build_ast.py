import argparse

from antlr4 import FileStream

from wrappers import ParseTreeWrapper

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Path to query language script for parsing')
    parser.add_argument('-o', '--output', help='Path to output Abstract Syntax Tree (.dot graph representation)')
    parser.add_argument('-v', '--view', action='store_true', help='Open graph in the PDF view immediately')
    args = parser.parse_args()
    wrapper = ParseTreeWrapper(FileStream(args.input))
    if wrapper.ast is not None:
        wrapper.graph.render(args.output, view=args.view)
