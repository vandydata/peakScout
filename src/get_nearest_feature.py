import pandas as pd
import numpy as np
import os

def read_input(data_dir, file, peak_type):
    if peak_type == 'MACS2':
        return read_input_MACS2(data_dir, file)
    elif peak_type == 'SEACR':
        return read_input_SEACR(data_dir, file)

def read_input_MACS2(data_dir, file):
    peaks = pd.read_csv(data_dir + file, sep = '\t', skiprows=22)
    peaks.rename(columns={'-log10(pvalue)': 'neg_log10_pvalue', '-log10(qvalue)': 'neg_log10_qvalue'}, inplace=True)

    return peaks

def read_input_SEACR(data_dir, file):
    peaks = pd.read_csv(data_dir + file, sep = '\t', skiprows=22)
    peaks.rename(columns={'-log10(pvalue)': 'neg_log10_pvalue', '-log10(qvalue)': 'neg_log10_qvalue'}, inplace=True)

    return peaks

def process_input_MACS2(data, qval = 0.05, option = 'native_peak_boundaries', 
                  boundary = None, num_peaks_cutoff = None):
    
    peaks = data.loc[data['neg_log10_qvalue'] > -np.log10(qval)]
    peaks.sort_values(by = 'neg_log10_qvalue', ascending=False, inplace=True)

    if num_peaks_cutoff is not None:
        peaks = peaks.head(num_peaks_cutoff)

    if option == 'peak_summit':
        peaks['start'] = peaks['abs_summit']
        peaks['end'] = peaks['abs_summit']
    elif option == 'artifical_peak_boundaries' and boundary is not None:
        peaks['start'] = peaks['abs_summit'] - boundary
        peaks['end'] = peaks['abs_summit'] + boundary
    elif option == 'native_peak_boundaries':
        pass
    else:
        raise ValueError('Invalid peak start/end option')
    
    return peaks

def decompose_peaks(peaks):
    return {'chr' + name: group for name, group in peaks.groupby(['chr'], group_keys=False)}

def gen_output(decomposed_peaks, species, feature_type, num_features, ref_dir):
    for key in decomposed_peaks.keys():
        features = pd.read_csv(ref_dir + species + "/" + feature_type + "/" + key)
        output = pd.concat([output, get_nearest_features(decomposed_peaks[key], features, num_features)], 
                        ignore_index = False, sort = False)

    if not os.path.exists("results/"):
        os.mkdir("results/")

    output.to_csv('results/nearest_genes.csv', index = False)

def get_nearest_features(roi, features, k):
    gene_starts = features['start'].values
    gene_ends = features['end'].values
    return_roi = roi.copy()

    for i in range(1, k+1):
        return_roi['closest_gene_' + str(i)] = None

    index = 0
    for _, peak in return_roi.iterrows():
        peak_start = peak['start']
        insert_index = gene_starts.searchsorted(peak_start, side='left')

        i = k
        downstream = insert_index
        upstream = insert_index - 1
        peak_end = peak['end']

        while i > 0 and upstream > -1 and downstream < len(features):
            downstream_dist = gene_starts[downstream] - peak_end
            upstream_dist = peak_start - gene_ends[upstream]
            closest = None

            if downstream_dist < upstream_dist:
                closest = downstream
                downstream += 1
            else:
                closest = upstream
                upstream -= 1
                
            return_roi.iloc[index, len(return_roi.columns) - i] = features.iloc[closest, :]['name']
            i -= 1
        
        if i > 0 and upstream < 0:
            while i > 0 and downstream < len(features):
                return_roi.iloc[index, len(return_roi.columns) - i] = features.iloc[downstream, :]['name']
                downstream += 1
                i -= 1
        elif i > 0 and downstream >= len(features):
            while i > 0 and upstream > -1:
                return_roi.iloc[index, len(return_roi.columns) - i] = features.iloc[upstream, :]['name']
                upstream -= 1
                i -= 1

        index += 1

    return return_roi
 
# data information
data_dir = "test/"
ref_dir = "reference/"

# function parameters
num_peaks_cutoff = None 
num_nearest_features = 3

# Set peak boundary options
# a. "native_peak_boundaries" - use start + end of peak, as defined by peak caller
# b. "peak_summit" - use peak summit
# c. "artificial_peak_boundaries" - use artificial boundary, such as +/-100 bp from peak summit
option = "native_peak_boundaries"
boundary = None

peaks = read_input(data_dir, 'MACS2_peaks.xls', 'MACS2')
peaks = process_input_MACS2(peaks)
decomposed_peaks = decompose_peaks(peaks)
gen_output(decomposed_peaks, "mm10", "gene", 3, ref_dir)


# peaks = pd.read_csv('data/Pdx1_1_100_R1.macs2_peaks.xls', sep='\t', skiprows=22)
# peaks.rename(columns={'-log10(pvalue)': 'neg_log10_pvalue', '-log10(qvalue)': 'neg_log10_qvalue'}, inplace=True)

# # filter peaks where qval > 0.05 and cutoff (if necessary)
# peaks = peaks.loc[peaks['neg_log10_qvalue'] > 1.3]
# peaks.sort_values(by = 'neg_log10_qvalue', ascending=False, inplace=True)

# if num_peaks_cutoff is not None:
#     peaks = peaks.head(num_peaks_cutoff)

# # modify start and end columns
# if option == 'peak_summit':
#     peaks['start'] = peaks['abs_summit']
#     peaks['end'] = peaks['abs_summit']
# elif option == 'artifical_peak_boundaries':
#     peaks['start'] = peaks['abs_summit'] - boundary
#     peaks['end'] = peaks['abs_summit'] + boundary
# elif option == 'native_peak_boundaries':
#     pass
# else:
#     raise ValueError('Invalid peak start/end option')

# # split peaks by chromosome
# peaks_by_chr = {i: peaks.loc[peaks['chr'] == str(i)] for i in range(1, num_chr)}
# peaks_by_chr['X'] = peaks.loc[peaks['chr'] == "X"]
# peaks_by_chr['Y'] = peaks.loc[peaks['chr'] == "Y"]
# peaks_by_chr['M'] = peaks.loc[peaks['chr'] == "M"]

# ###################################################################################################
# valid_chr = ['chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9', 'chrM', 'chrX', 
#              'chrY', 'chr10', 'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17', 'chr18', 'chr19']
# desired_cols = ['name', 'chrom', 'start', 'end']
# start_name = 'txStart'
# end_name = 'txEnd'

# genes = pd.read_csv('data/mm10.csv', sep='\t')

# genes.rename(columns={'#name': 'name', start_name: 'start', end_name: 'end'}, inplace=True)
# genes = genes.loc[genes['chrom'].isin(valid_chr)][desired_cols]

# genes_by_chr = {i: genes.loc[genes['chrom'] == "chr" + str(i)].sort_values(by = 'start') for i in range(1, num_chr)}
# genes_by_chr['X'] = genes.loc[genes['chrom'] == "chrX"]
# genes_by_chr['Y'] = genes.loc[genes['chrom'] == "chrY"]
# genes_by_chr['M'] = genes.loc[genes['chrom'] == "chrM"]

# output = pd.DataFrame()
# for key in peaks_by_chr.keys():
#     output = pd.concat([output, get_nearest_features(peaks_by_chr[key], genes_by_chr[key], num_nearest_features)], 
#                        ignore_index = False, sort = False)

# output.to_csv('results/nearest_genes.csv', index = False)

