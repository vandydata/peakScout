import polars as pl
import os

def decompose_df(ref_dir, species, full_ref, col_names):
    if not os.path.exists(ref_dir + species):
        os.mkdir(ref_dir + species)

    full_df = pl.read_csv(ref_dir + species + "/" + full_ref, has_header=False, separator="\t", skip_rows=5, new_columns=col_names)

    for name, group in full_df.group_by(['type']):
        group = split_jumble(group)

        decomposed_dfs_start = {(chr[0], name[0]): chr_group.sort('start').unique(subset='start')
                                 for chr, chr_group in group.group_by(['chr'])}
        save_csvs(decomposed_dfs_start, species, 'start')

        decomposed_dfs_end = {chr_name: chr_group.sort('end') 
                              for chr_name, chr_group in decomposed_dfs_start.items()}
        save_csvs(decomposed_dfs_end, species, 'end')

def save_csvs(df, species, col):
    for name, group in df.items():
        chr = name[0]
        type_name = name[1]
        if not os.path.exists(ref_dir + species + "/" + type_name):
            os.mkdir(ref_dir + species + "/" + type_name)

        group.write_csv(ref_dir + species + "/" + type_name + "/" + chr + '_' + col + '.csv') 
        print(name)

def split_jumble(df):
    jumble_data = df.select('info')

    unique_keys = set()

    for row in jumble_data.to_numpy():
        keys = [pair.split(' ')[0] for pair in row[0].split('; ')]
        unique_keys.update(keys)
    
    cols_to_add = {key: [] for key in unique_keys}
    for row in jumble_data.iter_rows(named=True):
        key_value = {pair.split(' ')[0]: pair.split(' ')[1].replace('"', '').replace(';', '') 
                    for pair in row['info'].split('; ')}
        for key in unique_keys:
            try:
                cols_to_add[key].append(key_value[key])
            except:
                cols_to_add[key].append(None)
    
    for name, group in cols_to_add.items():
        df.insert_column(-1, pl.Series(name, group))
    

    df.drop_in_place('info')

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

