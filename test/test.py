import polars as pl
import numpy as np
import os

def peak2gene(file_path, peak_type, species, feature_type, num_features, ref_dir, output_name,
              option = 'native_peak_boundaries', boundary = None, num_peaks_cutoff = None, 
              up_bound = None, down_bound = None):
    if peak_type == 'MACS2' and 'xls' in file_path:
        peaks = read_input_MACS2_xls(file_path)
        peaks = process_input_MACS2_xls(peaks)
    elif peak_type == 'MACS2' and 'bed' in file_path:
        peaks = read_input_MACS2_bed(file_path)
        peaks = process_input_MACS2_bed(peaks)
    elif peak_type == 'SEACR':
        peaks = read_input_SEACR(file_path)
        peaks = process_input_SEACR(peaks)
    else:
        raise TypeError('Invalid peak type')

    if 'bed' in file_path:
        peaks = peaks.with_columns(pl.col('start') + 1)
        peaks = peaks.with_columns(pl.col('end') + 1)

    
    decomposed_peaks = decompose_peaks(peaks)
    gen_output(decomposed_peaks, species, feature_type, num_features, ref_dir, output_name, up_bound,
               down_bound)

def read_input_MACS2_xls(file_path):
    peaks = pl.read_csv(file_path, separator = '\t', skip_rows=22)
    peaks = peaks.rename({'-log10(pvalue)': 'neg_log10_pvalue', '-log10(qvalue)': 'neg_log10_qvalue'})

    return peaks

def read_input_MACS2_bed(file_path):
    col_names = ['chr', 'start', 'end', 'name', 'signal', 'pvalue', 'qvalue', 'peak']
    peaks = pl.read_csv(file_path, has_header= False, separator = '\t', new_columns=col_names[:5])

    return peaks

def read_input_SEACR(file_path):
    col_names = ['chr', 'start', 'end', 'name', 'score', 'region']
    peaks = pl.read_csv(file_path, separator = '\t', new_columns=col_names)

    return peaks

def process_input_MACS2_xls(data, qval = None, option = 'native_peak_boundaries', 
                  boundary = None, num_peaks_cutoff = None):
    peaks = data
    if qval is not None:
        peaks = data.select(threshold = pl.when(data.col('neg_log10_qvalue') > -np.log10(qval)))
        peaks = peaks.sort('neg_log10_qvalue', descending=True)

    if num_peaks_cutoff is not None:
        peaks = peaks.head(num_peaks_cutoff)

    if option == 'peak_summit':
        peaks.drop_in_place('start')
        peaks.with_columns((peaks.col('abs_summit')).alias('start'))
        peaks.drop_in_place('end')
        peaks.with_columns((peaks.col('abs_summit')).alias('end'))
    elif option == 'artifical_peak_boundaries' and boundary is not None:
        peaks.drop_in_place('start')
        peaks.with_columns((peaks.col('abs_summit') - boundary).alias('start'))
        peaks.drop_in_place('end')
        peaks.with_columns((peaks.col('abs_summit') + boundary).alias('end'))
    elif option == 'native_peak_boundaries':
        pass
    else:
        raise ValueError('Invalid peak start/end option')
    
    return peaks

def process_input_MACS2_bed(data, score = 0.05, option = 'native_peak_boundaries', 
                  boundary = None, num_peaks_cutoff = None):
    
    peaks = data

    if num_peaks_cutoff is not None:
        peaks = peaks.head(num_peaks_cutoff)

    if option == 'peak_summit':
        peaks.drop_in_place('start')
        peaks.with_columns((peaks.col('abs_summit')).alias('start'))
        peaks.drop_in_place('end')
        peaks.with_columns((peaks.col('abs_summit')).alias('end'))
    elif option == 'artifical_peak_boundaries' and boundary is not None:
        peaks.drop_in_place('start')
        peaks.with_columns((peaks.col('abs_summit') - boundary).alias('start'))
        peaks.drop_in_place('end')
        peaks.with_columns((peaks.col('abs_summit') + boundary).alias('end'))
    elif option == 'native_peak_boundaries':
        pass
    else:
        raise ValueError('Invalid peak start/end option')
    
    return peaks

def process_input_SEACR(data, signal = None, option = 'native_peak_boundaries',
                        boundary = None, num_peaks_cutoff = None):
    peaks = data
    if signal is not None:
        peaks = data.select(threshold = pl.where(data.col('signal') > signal))
    # peaks.sort_values(by = 'neg_log10_qvalue', ascending=False, inplace=True)

    if num_peaks_cutoff is not None:
        peaks = peaks.head(num_peaks_cutoff)

    if option == 'peak_summit':
        peaks.drop_in_place('start')
        peaks.with_columns((peaks.col('abs_summit')).alias('start'))
        peaks.drop_in_place('end')
        peaks.with_columns((peaks.col('abs_summit')).alias('end'))
    elif option == 'artifical_peak_boundaries' and boundary is not None:
        peaks.drop_in_place('start')
        peaks.with_columns((peaks.col('abs_summit') - boundary).alias('start'))
        peaks.drop_in_place('end')
        peaks.with_columns((peaks.col('abs_summit') + boundary).alias('end'))
    elif option == 'native_peak_boundaries':
        pass
    else:
        raise ValueError('Invalid peak start/end option')
    
    return peaks

def decompose_peaks(peaks):
    return {'chr' + str(name[0]) if 'chr' not in str(name[0]) else str(name[0]): 
            group for name, group in peaks.group_by(['chr'])}

def gen_output(decomposed_peaks, species, feature_type, num_features, ref_dir, output_name,
               up_bound, down_bound):
    output = pl.DataFrame()
    for key in decomposed_peaks.keys():
        starts = pl.read_csv(ref_dir + species + "/" + feature_type + "/" + key + '_start.csv')
        ends = pl.read_csv(ref_dir + species + "/" + feature_type + "/" + key + '_end.csv')
        output = pl.concat([output, get_nearest_features(decomposed_peaks[key], 'gene_name', starts, ends,
                                                         up_bound, down_bound, num_features)])

    if not os.path.exists("test/results/"):
        os.mkdir("test/results/")
    
    output = output.sort(['chr', 'start'])
    output.drop_in_place('start')
    output.drop_in_place('end')
    output.drop_in_place('chr')
    output.drop_in_place('name')
    
    custom_columns = ['peak1', 'peak2', 'peak3', 'peak4', 'peak5', 'peak6', 'peak7',
                      'peak8', 'peak9', 'peak10']
    output.insert_column(0, pl.Series('name', custom_columns))
    output.write_csv('test/results/test_actual.csv')

def get_nearest_features(roi, feature, starts, ends, up_bound, down_bound, k):
    feature_starts = starts.select(['start','end']).to_numpy()
    feature_ends = ends.select('end').to_numpy().flatten()
    assert(len(feature_starts) == len(feature_ends))

    start_features = starts.select(feature).to_numpy().flatten()
    end_features = ends.select(feature).to_numpy().flatten()

    return_roi = roi.select(['name', 'chr', 'start', 'end']).clone()

    index = 0
    features_to_add = {}

    for i in range(1, k+1):
        features_to_add[i] = []

    for peak in return_roi.iter_rows(named=True):
        peak_start = peak['start']
        peak_end = peak['end']

        downstream_start, downstream_bound, upstream_bound, upstream_end = constrain_features(feature_starts, feature_ends, 
                                                                                              down_bound, up_bound,
                                                                                              peak_start, peak_end)
        
        # print(downstream_bound, upstream_bound)
        constrained_feature_starts = feature_starts[downstream_start : downstream_bound]
        constrained_feature_ends = feature_ends[upstream_bound : upstream_end]

        constrained_starts = start_features[downstream_start : downstream_bound]
        constrained_ends = end_features[upstream_bound : upstream_end]

        downstream_index = 0 #constrained_starts.searchsorted(peak_start, side='left')
        upstream_index = len(constrained_ends) - 1 #constrained_ends.searchsorted(peak_end, side='right') - 1

        assert(len(constrained_starts) == len(constrained_feature_starts))
        assert(len(constrained_ends) == len (constrained_feature_ends))

        overlap_genes = []
        overlap_index = 0
        while len(constrained_feature_starts) > overlap_index and constrained_feature_starts[overlap_index][0] <= peak_end:
            if constrained_feature_starts[overlap_index][0] <= peak_start  \
                and constrained_feature_starts[overlap_index][1] >= peak_start:
                overlap_genes.append(overlap_index)
            elif constrained_feature_starts[overlap_index][0] <= peak_end  \
                and constrained_feature_starts[overlap_index][1] >= peak_end:
                overlap_genes.append(overlap_index)
            overlap_index += 1
        
        i = k
        zero_index = 0

        while(zero_index < len(overlap_genes) and i > 0):
            features_to_add[k-i+1].append(constrained_starts[overlap_genes[zero_index]])
            # dists_to_add[k-i+1].append(str(0))
            zero_index += 1
            i -= 1

        while i > 0 and upstream_index > -1 and downstream_index < len(constrained_starts):
            downstream_dist = constrained_feature_starts[downstream_index][0] - peak_end
            upstream_dist = peak_start - constrained_feature_ends[upstream_index]

            downstream_dist = 0 if downstream_dist < 0 else downstream_dist
            upstream_dist = 0 if upstream_dist < 0 else upstream_dist

            if downstream_dist == 0:
                downstream_index += 1
                continue
            
            if upstream_dist == 0:
                upstream_index -= 1
                continue

            if downstream_dist < upstream_dist:
                features_to_add[k-i+1].append(constrained_starts[downstream_index])
                # dists_to_add[k-i+1].append(str(downstream_dist))
                downstream_index += 1
            else:
                features_to_add[k-i+1].append(constrained_ends[upstream_index])
                # dists_to_add[k-i+1].append(str(-1 * upstream_dist))
                upstream_index -= 1
        
            i -= 1
        
        if i > 0 and upstream_index < 0:
            while i > 0 and downstream_index < len(constrained_starts):
                features_to_add[k-i+1].append(constrained_starts[downstream_index])
                downstream_dist = constrained_feature_starts[downstream_index][0] - peak_end
                downstream_dist = 0 if downstream_dist < 0 else downstream_dist
                # dists_to_add[k-i+1].append(str(downstream_dist))
                downstream_index += 1
                i -= 1
        elif i > 0 and downstream_index >= len(constrained_starts):
            while i > 0 and upstream_index > -1:
                features_to_add[k-i+1].append(constrained_ends[upstream_index])
                upstream_dist = peak_start - constrained_feature_ends[upstream_index]
                upstream_dist = 0 if upstream_dist < 0 else upstream_dist
                # dists_to_add[k-i+1].append(str(-1 * upstream_dist))
                upstream_index -= 1
                i -= 1
        
        while i > 0:
            features_to_add[k-i+1].append("N/A")
            # dists_to_add[k-i+1].append("N/A")
            i -= 1

        index += 1
    
    for i in range(1, k+1):
        if feature == 'gene_name':
            return_roi = return_roi.with_columns([pl.Series('closest_' + feature + '_' + str(i), features_to_add[i])])#,
                                            #   pl.Series('closest_' + 'gene' + '_' + str(i) + '_dist', dists_to_add[i])])
        else: 
            return_roi = return_roi.with_columns([pl.Series('closest_' + feature + '_' + str(i), features_to_add[i])])#,
                                            #   pl.Series('closest_' + feature + '_' + str(i) + '_dist', dists_to_add[i])])

    return return_roi

def constrain_features(feature_starts, feature_ends, down_bound, up_bound, peak_start, peak_end):
    if down_bound is not None:
        downstream_bound = feature_starts.searchsorted(peak_end + down_bound, side='right')
    else:
        downstream_bound = len(feature_starts)
    
    if up_bound is not None:
        upstream_bound = feature_ends.searchsorted(peak_start - up_bound, side='left')
    else:
        upstream_bound = 0
    
    downstream_start = 0
    upstream_end = feature_ends.searchsorted(peak_end, side='right')

    return downstream_start, downstream_bound, upstream_bound, upstream_end

 
# data information
data_dir = "test/"
ref_dir = "test/test-reference/"

# function parameters
num_peaks_cutoff = None 
num_nearest_features = 3

# Set peak boundary options
# a. "native_peak_boundaries" - use start + end of peak, as defined by peak caller
# b. "peak_summit" - use peak summit
# c. "artificial_peak_boundaries" - use artificial boundary, such as +/-100 bp from peak summit
option = "native_peak_boundaries"
boundary = None

# for file in os.listdir(data_dir):
#     # if "macs2" in file or "MACS2" in file:
#     if "MACS2" in file:
#         peak2gene(data_dir + file, 'MACS2', "mm10", "gene", 3, ref_dir, file[:-4], up_bound = 5000, down_bound = 5000)
#     # if "seacr" in file or "SEACR" in file:
#     #     peakScout(data_dir + file, 'SEACR', "mm10", "gene", 3, ref_dir, file[:-4])

file = "test_MACS2.bed"
peak2gene(data_dir + file, 'MACS2', "test", "gene", 3, ref_dir, file[:-4])