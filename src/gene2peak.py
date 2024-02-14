import pandas as pd
import polars as pl
import numpy as np
import os
from openpyxl.styles import PatternFill
from openpyxl.worksheet.filters import FilterColumn, Filters
from openpyxl.utils import get_column_letter
from get_nearest_feature import get_nearest_features

def peak2gene(file_path, peak_type, species, feature_type, num_features, ref_dir, output_name,
              option = 'native_peak_boundaries', boundary = None, num_peaks_cutoff = None):
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
        peaks['start'] = peaks['start'] + 1
        peaks['end'] = peaks['end'] + 1
    
    decomposed_peaks = decompose_peaks(peaks)
    gen_output(decomposed_peaks, species, feature_type, num_features, ref_dir, output_name)

def read_input_MACS2_xls(file_path):
    peaks = pl.read_csv(file_path, separator = '\t', skip_rows=22)
    peaks = peaks.rename({'-log10(pvalue)': 'neg_log10_pvalue', '-log10(qvalue)': 'neg_log10_qvalue'})

    return peaks

def read_input_MACS2_bed(file_path):
    col_names = ['chr', 'start', 'end', 'name', 'score', 'ph']
    peaks = pl.read_csv(file_path, header = False, separator = '\t', new_columns=col_names)

    return peaks

def read_input_SEACR(file_path):
    col_names = ['chr', 'start', 'end', 'name', 'max_signal', 'max_signal_region']
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
    return {'chr' + str(name): group for name, group in peaks.group_by('chr')}

def gen_output(decomposed_peaks, species, feature_type, num_features, ref_dir, output_name):
    output = pl.DataFrame()
    for key in decomposed_peaks.keys():
        starts = pl.read_csv(ref_dir + species + "/" + feature_type + "/" + key + '_start.csv')
        ends = pl.read_csv(ref_dir + species + "/" + feature_type + "/" + key + '_end.csv')
        output = pl.concat([output, get_nearest_features(decomposed_peaks[key], starts, ends, num_features)])

    if not os.path.exists("results/"):
        os.mkdir("results/")
    
    output = output.to_pandas()
    output = output.sort_values(by=['chr', 'name'])

    with pd.ExcelWriter('results/' + output_name + '.xlsx', engine='openpyxl') as writer:
    
        output.to_excel(writer, sheet_name='Sheet1', index=False)

        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        for row_num in range(2, len(output) + 2):
            if row_num % 2 == 0:
                for col_num in range(1, output.shape[1] + 1):
                    cell = worksheet.cell(row=row_num, column=col_num)
                    cell.fill = PatternFill(start_color='E6E6E6', end_color='E6E6E6', fill_type='solid')
            else:
                for col_num in range(1, output.shape[1] + 1):
                    cell = worksheet.cell(row=row_num, column=col_num)
                    cell.fill = PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type='solid')

        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[get_column_letter(column[0].column)].width = adjusted_width


        unique_chr_values = output['chr'].unique()

        filters = worksheet.auto_filter
        filters.ref = "A1:A" + str(len(output) + 1)
        col = FilterColumn(colId=0)
        col.filters = Filters(filter=unique_chr_values.tolist())
        filters.filterColumn.append(col)

        # Save the Excel file
        workbook.save('results/' + output_name + '.xlsx')
 
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

for file in os.listdir(data_dir):
    # if "macs2" in file or "MACS2" in file:
    if "MACS2" in file:
        peak2gene(data_dir + file, 'MACS2', "mm10", "gene", 3, ref_dir, file[:-4])
    # if "seacr" in file or "SEACR" in file:
    #     peakScout(data_dir + file, 'SEACR', "mm10", "gene", 3, ref_dir, file[:-4])