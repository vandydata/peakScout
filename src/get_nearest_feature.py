import polars as pl

def get_nearest_features(roi, feature, starts, ends, up_bound, down_bound, k):
    feature_starts = starts.select(['start','end']).to_numpy()
    feature_ends = ends.select('end').to_numpy().flatten()
    assert(len(feature_starts) == len(feature_ends))

    start_features = starts.select(feature).to_numpy().flatten()
    end_features = ends.select(feature).to_numpy().flatten()

    return_roi = None
    if 'name' in roi.columns:
        return_roi = roi.select(['name', 'chr', 'start', 'end']).clone()
    else:
        return_roi = roi.select(['chr', 'start', 'end']).clone()

    index = 0
    features_to_add = {}
    dists_to_add = {}
    for i in range(1, k+1):
        features_to_add[i] = []
        dists_to_add[i] = []

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
            dists_to_add[k-i+1].append(str(0))
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
                dists_to_add[k-i+1].append(str(downstream_dist))
                downstream_index += 1
            else:
                features_to_add[k-i+1].append(constrained_ends[upstream_index])
                dists_to_add[k-i+1].append(str(-1 * upstream_dist))
                upstream_index -= 1
        
            i -= 1
        
        if i > 0 and upstream_index < 0:
            while i > 0 and downstream_index < len(constrained_starts):
                features_to_add[k-i+1].append(constrained_starts[downstream_index])
                downstream_dist = constrained_feature_starts[downstream_index][0] - peak_end
                downstream_dist = 0 if downstream_dist < 0 else downstream_dist
                dists_to_add[k-i+1].append(str(downstream_dist))
                downstream_index += 1
                i -= 1
        elif i > 0 and downstream_index >= len(constrained_starts):
            while i > 0 and upstream_index > -1:
                features_to_add[k-i+1].append(constrained_ends[upstream_index])
                upstream_dist = peak_start - constrained_feature_ends[upstream_index]
                upstream_dist = 0 if upstream_dist < 0 else upstream_dist
                dists_to_add[k-i+1].append(str(-1 * upstream_dist))
                upstream_index -= 1
                i -= 1
        
        while i > 0:
            features_to_add[k-i+1].append("N/A")
            dists_to_add[k-i+1].append("N/A")
            i -= 1

        index += 1
    
    for i in range(1, k+1):
        if feature == 'gene_name':
            return_roi = return_roi.with_columns([pl.Series('closest_' + feature + '_' + str(i), features_to_add[i]),
                                              pl.Series('closest_' + 'gene' + '_' + str(i) + '_dist', dists_to_add[i])])
        else: 
            return_roi = return_roi.with_columns([pl.Series('closest_' + feature + '_' + str(i), features_to_add[i]),
                                              pl.Series('closest_' + feature + '_' + str(i) + '_dist', dists_to_add[i])])

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
