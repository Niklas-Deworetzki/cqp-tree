import sys
from cqp_tree.translation import cqp_from_query
from cqp_tree.grew import query_from_grew


def main():
    if len(sys.argv) != 2:
        print(f'Usage: cqp-tree <filename>')
        print('Read a file containing a Grew query and print the equivalent CQP query.')
        sys.exit(1)

    with open(sys.argv[1]) as f:
        query = query_from_grew(f.read())
        cqp = cqp_from_query(query)
        print(str(cqp))


if __name__ == '__main__':
    main()
