import polars as pl

def get_nearest_features(roi, starts, ends, k):
    gene_starts = starts.select('start').to_numpy().flatten()
    gene_ends = ends.select('end').to_numpy().flatten()
    assert(len(gene_starts) == len(gene_ends))

    return_roi = None
    if 'name' in roi.columns:
        return_roi = roi.select(['chr', 'name', 'start', 'end']).clone()
    else:
        return_roi = roi.select(['chr', 'start', 'end']).clone()

    index = 0
    genes_to_add = {}
    dists_to_add = {}
    for i in range(1, k+1):
        genes_to_add[i] = []
        dists_to_add[i] = []

    for peak in return_roi.iter_rows(named=True):
        peak_start = peak['start']
        peak_end = peak['end']
        downstream_index = gene_starts.searchsorted(peak_start, side='left')
        upstream_index = gene_ends.searchsorted(peak_end, side='right') - 1
        i = k

        while i > 0 and upstream_index > -1 and downstream_index < len(starts):
            downstream_dist = gene_starts[downstream_index] - peak_end
            upstream_dist = peak_start - gene_ends[upstream_index]

            downstream_dist = 0 if downstream_dist < 0 else downstream_dist
            upstream_dist = 0 if upstream_dist < 0 else upstream_dist

            if downstream_dist < upstream_dist:
                genes_to_add[k-i+1].append(starts.row(downstream_index, named=True)['gene_name'])
                dists_to_add[k-i+1].append(downstream_dist)
                downstream_index += 1
            else:
                genes_to_add[k-i+1].append(ends.row(upstream_index, named=True)['gene_name'])
                dists_to_add[k-i+1].append(upstream_dist)
                upstream_index -= 1
        
            i -= 1
        
        if i > 0 and upstream_index < 0:
            while i > 0 and downstream_index < len(starts):
                genes_to_add[k-i+1].append(starts.row(downstream_index, named=True)['gene_name'])
                dists_to_add[k-i+1].append(downstream_dist)
                downstream_index += 1
                i -= 1
        elif i > 0 and downstream_index >= len(ends):
            while i > 0 and upstream_index > -1:
                genes_to_add[k-i+1].append(ends.row(upstream_index, named=True)['gene_name'])
                dists_to_add[k-i+1].append(upstream_dist)
                upstream_index -= 1
                i -= 1

        index += 1
    
    for i in range(1, k+1):
        return_roi = return_roi.with_columns([pl.Series('closest_gene_' + str(i), genes_to_add[i]),
                                              pl.Series('closest_gene_' + str(i) + '_dist', dists_to_add[i])])

    return return_roi
