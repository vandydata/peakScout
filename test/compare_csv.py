import csv
import argparse


def main(args):
    actual = args.actual
    expected = args.expected

    compare_csv_files(actual, expected)


def compare_csv_files(file1, file2):
    with open(file1, "r") as f1, open(file2, "r") as f2:
        reader1 = csv.reader(f1)
        reader2 = csv.reader(f2)

        rows1 = list(reader1)
        rows2 = list(reader2)

    headers1 = rows1[0]
    headers2 = rows2[0]
    if headers1 != headers2:
        return False, "Headers are different"

    rows1 = set(tuple(row) for row in rows1[1:])
    rows2 = set(tuple(row) for row in rows2[1:])

    if rows1 == rows2:
        return True, "Files are identical"
    else:
        raise Exception("CSV files different")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="peakScount: find nearest features")

    parser.add_argument("--actual", "--a", type=str, help="Path to actual csv")
    parser.add_argument("--expected", "--e", type=str, help="Path to expected csv")

    args = parser.parse_args()

    main(args)
