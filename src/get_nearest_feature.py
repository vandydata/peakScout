import polars as pl

def get_nearest_features(roi, feature, starts, ends, k):
    feature_starts = starts.select('start').to_numpy().flatten()
    feature_ends = ends.select('end').to_numpy().flatten()
    assert(len(feature_starts) == len(feature_ends))

    return_roi = None
    if 'name' in roi.columns:
        return_roi = roi.select(['chr', 'name', 'start', 'end']).clone()
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
        downstream_index = feature_starts.searchsorted(peak_start, side='left')
        upstream_index = feature_ends.searchsorted(peak_end, side='right') - 1
        i = k

        while i > 0 and upstream_index > -1 and downstream_index < len(starts):
            downstream_dist = feature_starts[downstream_index] - peak_end
            upstream_dist = peak_start - feature_ends[upstream_index]

            downstream_dist = 0 if downstream_dist < 0 else downstream_dist
            upstream_dist = 0 if upstream_dist < 0 else upstream_dist

            if downstream_dist < upstream_dist:
                features_to_add[k-i+1].append(starts.row(downstream_index, named=True)[feature])
                dists_to_add[k-i+1].append(downstream_dist)
                downstream_index += 1
            else:
                features_to_add[k-i+1].append(ends.row(upstream_index, named=True)[feature])
                dists_to_add[k-i+1].append(upstream_dist)
                upstream_index -= 1
        
            i -= 1
        
        if i > 0 and upstream_index < 0:
            while i > 0 and downstream_index < len(starts):
                features_to_add[k-i+1].append(starts.row(downstream_index, named=True)[feature])
                dists_to_add[k-i+1].append(downstream_dist)
                downstream_index += 1
                i -= 1
        elif i > 0 and downstream_index >= len(ends):
            while i > 0 and upstream_index > -1:
                features_to_add[k-i+1].append(ends.row(upstream_index, named=True)[feature])
                dists_to_add[k-i+1].append(upstream_dist)
                upstream_index -= 1
                i -= 1

        index += 1
    
    for i in range(1, k+1):
        return_roi = return_roi.with_columns([pl.Series('closest_' + feature + '_' + str(i), features_to_add[i]),
                                              pl.Series('closest_' + feature + '_' + str(i) + '_dist', dists_to_add[i])])

    return return_roi
