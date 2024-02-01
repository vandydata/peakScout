import pandas as pd
import os

def decompose_df(ref_dir, species, full_ref, col_names):
    full_df = pd.read_csv(ref_dir + species + "/" + full_ref, sep = "\t", skiprows=5, names = col_names)

    decomposed_dfs = {name: group for name, group in full_df.groupby(['chr', 'type'], group_keys=False)}

    for name, group in decomposed_dfs.items():
        chr = name[0]
        type_name = name[1]
        if not os.path.exists(ref_dir + species + "/" + type_name):
            os.mkdir(ref_dir + species + "/" + type_name)
    
        group.to_csv(ref_dir + species + "/" + type_name + "/" + chr)

ref_dir = 'reference/'
mm10_ref = 'gencode.vM25.annotation.gtf'
col_names = ['chr', 'source', 'type', 'start', 'end', 'ph1', 'strand', 'ph2', 'info']

decompose_df(ref_dir, "mm10", mm10_ref, col_names)

# mm10_df = pd.read_csv(ref_dir + mm10_ref, sep = '\t', skiprows=5, names=col_names)

# decomposed_dfs = {(chr, type_name): group for (chr, type_name), group in mm10_df.groupby(['chr', 'type'], group_keys=False)}

# for name, group in decomposed_dfs.items():
#     chr = name[0]
#     type_name = name[1]
#     if not os.path.exists(ref_dir + type_name):
#         os.mkdir(ref_dir + type_name)
    
#     group.to_csv(ref_dir + type_name + "/" + chr)

        

