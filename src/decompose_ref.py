import pandas as pd
import os

def decompose_df(ref_dir, species, full_ref, col_names):
    if not os.path.exists(ref_dir + species):
        os.mkdir(ref_dir + species)

    full_df = pd.read_csv(ref_dir + species + "/" + full_ref, sep = "\t", skiprows=5, names = col_names)

    decomposed_dfs_start = {name: group.sort_values(by = 'start') for name, group in full_df.groupby(['chr', 'type'], group_keys=False)}
    decomposed_dfs_end = {name: group.sort_values(by = 'end') for name, group in full_df.groupby(['chr', 'type'], group_keys=False)}

    for name, group in decomposed_dfs_start.items():
        chr = name[0]
        type_name = name[1]
        if not os.path.exists(ref_dir + species + "/" + type_name):
            os.mkdir(ref_dir + species + "/" + type_name)

        group = split_jumble(group)
        group.drop_duplicates(subset='start', keep='first', inplace=True)
        group.to_csv(ref_dir + species + "/" + type_name + "/" + chr + '-start.csv') 
        print(name)

    for name, group in decomposed_dfs_end.items():
        chr = name[0]
        type_name = name[1]
        if not os.path.exists(ref_dir + species + "/" + type_name):
            os.mkdir(ref_dir + species + "/" + type_name)

        group = split_jumble(group)
        group.drop_duplicates(subset='start', keep='first', inplace=True)
        group.to_csv(ref_dir + species + "/" + type_name + "/" + chr + '_end.csv') 
        print(name)

def split_jumble(df):
    jumble_data = df['info']

    unique_keys = set()

    for row in jumble_data.to_numpy():
        keys = [pair.split(' ')[0] for pair in row.split('; ')]
        unique_keys.update(keys)
    
    for key in unique_keys:
        df[key] = None

    for index, row in jumble_data.to_frame().iterrows():
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

