import polars as pl
import os

def decompose_gtf(ref_dir: str, 
                  species: str, 
                  gtf_ref: str,
                  out_dir: str) -> None:
    '''
    Decompose a GTF file into its various features (i.e. gene, CDS, exon, etc.).
    Each feature is further decomposed by chromosome, and the start and end 
    positions of each feature are noted in the chromosomal csv files. 

    Parameters:
    ref_dir (str): The directory to store the GTF decompositions.
    species (str): The species to which the GTF corresponds.
    gtf_ref (str): The path to the GTF file.
    out_dir (str): The output directory of decomposed csvs.

    Returns:
    None

    Outputs:
    The function will produce decomposed csv files and their parent directories
    as follows:

                out_dir/feature/chr{i}_[start | end].csv

    where species is the species provided in the parameters, feature is the 
    particular feature being decomposed (i.e. gene, CDS, exon, etc), i ranges 
    from 1 to the total number of chromosomes (and can also include non-autosomes 
    such as X and Y and non-nuclear chromosomes such as M), and [start | end] means 
    that particular CSV file will contain the features sorted by either start or 
    end position.
    '''

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    col_names = ['chr', 'source', 'feature', 'start', 'end', 'score', 'strand', 'frame', 'attribute']

    full_df = pl.read_csv(gtf_ref, has_header=False, 
                          separator="\t", skip_rows=5, new_columns=col_names)

    for name, group in full_df.group_by(['feature']):
        group = split_jumble(group)

        decomposed_dfs_start = {(chr[0], name[0]): chr_group.sort('start').unique(subset='start')
                                 for chr, chr_group in group.group_by(['chr'])}
        save_csvs(decomposed_dfs_start, 'start', out_dir)

        decomposed_dfs_end = {chr_name: chr_group.sort('end') 
                              for chr_name, chr_group in decomposed_dfs_start.items()}
        save_csvs(decomposed_dfs_end, 'end', out_dir)

def save_csvs(df: pl.DataFrame, 
              col: str,
              out_dir: str) -> None:
    '''
    Save a given Polars DataFrame as a CSV file.

    Parameters:
    df (pl.DataFrame): The Polars DataFrame to save as a CSV file.
    col (str): The column of the GTF that this DataFrame is sorted by.
               This is either 'start' or 'end.'
    out_dir (str): The output directory of decomposed csvs.
    
    Returns:
    None

    Outputs:
    The function will save the Polars DataFrame as a CSV at location:

                out_dir/feature/chr{i}_[start | end].csv

    where reference is the specified reference directory in ref_dir, species
    is the species given in the parameters, i ranges from i to the number of chromosomes
    (and can include non-autosomes such as X, Y, and non-nuclear chromosomes such as M), and 
    start or end indicates that this CSV contains the features sorted by either start or end
    position, respectively. 
    '''

    for name, group in df.items():
        chr = name[0]
        type_name = name[1]
        if not os.path.exists(os.path.join(out_dir, type_name)):
            os.mkdir(os.path.join(out_dir, type_name))

        group.write_csv(os.path.join(out_dir, type_name, chr + '_' + col + '.csv')) 
        print(name)

def split_jumble(df: pl.DataFrame) -> pl.DataFrame:
    '''
    Splits the attribute column of the GTF and inserts them into the given Polars
    DataFrame as additional columns. After inserting all columns, the attribute 
    column is removed.

    Parameters:
    df (pl.DataFrame): The Polars DataFrame whose attribute column needs to be split.

    Returns:
    df (pl.DataFrame): The Polars DataFrame where each element in the original attribute
                       column is now its own column. The attribute column is also removed.
    
    Outputs:
    None
    '''

    jumble_data = df.select('attribute')

    unique_keys = set()

    for row in jumble_data.to_numpy():
        keys = [pair.split(' ')[0] for pair in row[0].split('; ')]
        unique_keys.update(keys)
    
    cols_to_add = {key: [] for key in unique_keys}
    for row in jumble_data.iter_rows(named=True):
        key_value = {pair.split(' ')[0]: pair.split(' ')[1].replace('"', '').replace(';', '') 
                    for pair in row['attribute'].split('; ')}
        for key in unique_keys:
            try:
                cols_to_add[key].append(key_value[key])
            except:
                cols_to_add[key].append(None)
    
    for name, group in cols_to_add.items():
        df.insert_column(-1, pl.Series(name, group))
    

    df.drop_in_place('attribute')

    return df

