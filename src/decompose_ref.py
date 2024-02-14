import pandas as pd
import polars as pl
import os

def decompose_df(ref_dir, species, full_ref, col_names):
    if not os.path.exists(ref_dir + species):
        os.mkdir(ref_dir + species)

    full_df = pd.read_csv(ref_dir + species + "/" + full_ref, sep = "\t", skiprows=5, names = col_names)
    # full_df = pl.read_csv(ref_dir + species + "/" + full_ref, separator="\t", skip_rows=5, columns=col_names)

    for name, group in full_df.groupby(by='type', group_keys=False):
    # for name, group in full_df.group_by('type'):
        print(name)
        group = split_jumble(group)

        decomposed_dfs_start = {(chr, name): chr_group.sort_values(by='start').drop_duplicates(subset='start')
                                 for chr, chr_group in group.groupby(by='chr', group_keys=False)}
        save_csvs(decomposed_dfs_start, species, 'start')

        decomposed_dfs_end = {inner_name: chr_group.sort_values(by='end') 
                              for inner_name, chr_group in decomposed_dfs_start.items()}
        save_csvs(decomposed_dfs_end, species, 'end')

def save_csvs(df, species, col):
    for name, group in df.items():
        chr = name[0]
        type_name = name[1]
        if not os.path.exists(ref_dir + species + "/" + type_name):
            os.mkdir(ref_dir + species + "/" + type_name)

        group.to_csv(ref_dir + species + "/" + type_name + "/" + chr + '_' + col + '.csv') 
        print(name)

def split_jumble(df):
    jumble_data = df['info']

    unique_keys = set()

    for row in jumble_data.to_numpy():
        keys = [pair.split(' ')[0] for pair in row.split('; ')]
        unique_keys.update(keys)
    
    for key in unique_keys:
        df[key] = None
    
    i = 1
    for index, row in jumble_data.to_frame().iterrows():
        if (index > i * 50000): 
            print(index)
            i += 1
        key_value = {pair.split(' ')[0]: pair.split(' ')[1].replace('"', '').replace(';', '') 
                    for pair in row['info'].split('; ')}
        for key in key_value.keys():
            df.loc[index, key] = key_value[key]
    
    del df['info']

    return df

ref_dir = 'reference/'
col_names = ['chr', 'source', 'type', 'start', 'end', 'ph1', 'strand', 'ph2', 'info']

mm10_ref = 'gencode.vM25.annotation.gtf'
decompose_df(ref_dir, "mm10", mm10_ref, col_names)

# mm39_ref = 'gencode.vM34.annotation.gtf'
# decompose_df(ref_dir, "mm39", mm39_ref, col_names)

# hg19_ref = 'gencode.v19.annotation.gtf'
# decompose_df(ref_dir, "hg19", hg19_ref, col_names)

# hg38_ref = 'gencode.v45.annotation.gtf'
# decompose_df(ref_dir, "hg38", hg38_ref, col_names)

