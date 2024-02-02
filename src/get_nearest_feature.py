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
    col_names = ['chr', 'start', 'end', 'total_signal', 'max_signal', 'max_signal_region']
    peaks = pd.read_csv(data_dir + file, sep = '\t', names=col_names)

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

def process_input_SEACR(data, signal = None, option = 'native_peak_boundaries',
                        boundary = None, num_peaks_cutoff = None):
    peaks = data
    if signal is not None:
        peaks = data.loc[data['signal'] > signal]
    # peaks.sort_values(by = 'neg_log10_qvalue', ascending=False, inplace=True)

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
    return {'chr' + str(name[0]): group for name, group in peaks.groupby(['chr'], group_keys=False)}

def gen_output(decomposed_peaks, species, feature_type, num_features, ref_dir, output_name):
    output = pd.DataFrame()
    for key in decomposed_peaks.keys():
        features = pd.read_csv(ref_dir + species + "/" + feature_type + "/" + key + '.csv')
        output = pd.concat([output, get_nearest_features(decomposed_peaks[key], features, num_features)], 
                        ignore_index = False, sort = False)

    if not os.path.exists("results/"):
        os.mkdir("results/")

    output.to_csv('results/' + output_name + '.csv', index = False)
    output.to_excel('results/' + output_name + '.xlsx', index = False)

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
                
            return_roi.iloc[index, len(return_roi.columns) - i] = features.iloc[closest, :]['gene_name']
            i -= 1
        
        if i > 0 and upstream < 0:
            while i > 0 and downstream < len(features):
                return_roi.iloc[index, len(return_roi.columns) - i] = features.iloc[downstream, :]['gene_name']
                downstream += 1
                i -= 1
        elif i > 0 and downstream >= len(features):
            while i > 0 and upstream > -1:
                return_roi.iloc[index, len(return_roi.columns) - i] = features.iloc[upstream, :]['gene_name']
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

macs2_peaks = read_input(data_dir, 'MACS2_peaks.xls', 'MACS2')
macs2_peaks = process_input_MACS2(macs2_peaks)
decomposed_macs2_peaks = decompose_peaks(macs2_peaks)
gen_output(decomposed_macs2_peaks, "mm10", "gene", 3, ref_dir, 'MACS2_peaks')

seacr_peaks = read_input(data_dir, 'SEACR_peaks.bed', 'SEACR')
seacr_peaks = process_input_SEACR(seacr_peaks)
decomposed_seacr_peaks = decompose_peaks(seacr_peaks)
gen_output(decomposed_seacr_peaks, "mm10", "gene", 3, ref_dir, 'SEACR_peaks')
