import argparse
from peak2gene import peak2gene

def main(args):
    function = args.function
    peak_file = args.peak_file
    peak_type = args.peak_type
    species = args.species
    k = args.num_features
    ref = args.ref_dir
    output_name = args.output_name
    out_dir = args.out_dir
    output_type = args.output_type
    option = args.option
    boundary = args.boundary
    ub = args.up_bound
    db = args.down_bound

    if function == 'peak2gene':
        peak2gene(peak_file, peak_type, species, k, ref, output_name, out_dir, output_type, option, boundary, ub, db)
    else:
        raise ValueError('Invalid peakScout call')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='peakScount: find nearest features')

    parser.add_argument('function', type=str, help='Function to run')
    parser.add_argument('--peak_file', type=str, help='Peak file')
    parser.add_argument('--peak_type', type=str, help='Peak type')
    parser.add_argument('--species', type=str, help='Species')
    parser.add_argument('--num_features', '--k', type=int, help='Number of features')
    parser.add_argument('--ref_dir', type=str, help='Reference directory')
    parser.add_argument('--output_name', type=str, help='Output name')
    parser.add_argument('--out_dir', '--o', '--out', type=str, dest='out_dir', help='Output directory')
    parser.add_argument('--output_type', type=str, help='Output type: csv or xlsx')
    parser.add_argument('--option', type=str, default='native_peak_boundaries', help='Option (default: native_peak_boundaries)')
    parser.add_argument('--boundary', type=int, default = None, help='Boundary (default: None)')
    parser.add_argument('--up_bound', '--ub', default = None, type=int, help='Up bound (default: None)')
    parser.add_argument('--down_bound', '--db', default = None, type=int, help='Down bound (default: None)')

    args = parser.parse_args()

    main(args)
