import csv

def compare_csv_files(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
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

actual_csv_file = "test/results/test_actual.csv"
expected_csv_file = "test/test_MACS2_expected_results.csv"

are_same, message = compare_csv_files(actual_csv_file, expected_csv_file)
print(message)
