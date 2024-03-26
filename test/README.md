# Test files

## Bed format
The BED format consists of one line per feature, each containing 3-12 columns of data, plus optional track definition lines.

Required fields

The first three fields in each feature line are required but typically 6 are used:

1. chrom - name of the chromosome or scaffold. Any valid seq_region_name can be used, and chromosome names can be given with or without the 'chr' prefix.
2. chromStart - Start position of the feature in standard chromosomal coordinates (i.e. first base is 0).
3. chromEnd - End position of the feature in standard chromosomal coordinates
4. name - Label to be displayed under the feature, if turned on in "Configure this page".
5. score - A score between 0 and 1000. See track lines, below, for ways to configure the display style of scored data.
6. strand - defined as + (forward) or - (reverse).

### narrowPeak

A narrowPeak (.narrowPeak) file is used by the ENCODE project to provide called peaks of signal enrichment based on pooled, normalized (interpreted) data. 

The narrowPeak file is a BED 6+4 format, which means the first 6 columns of a standard BED file with 4 additional fields:

1. chrom - name of the chromosome or scaffold. Any valid seq_region_name can be used, and chromosome names can be given with or without the 'chr' prefix.
2. chromStart - Start position of the feature in standard chromosomal coordinates (i.e. first base is 0).
3. chromEnd - End position of the feature in standard chromosomal coordinates
4. name - Label to be displayed under the feature, if turned on in "Configure this page".
5. score - A score between 0 and 1000. See track lines, below, for ways to configure the display style of scored data.
6. strand - defined as + (forward) or - (reverse).
7. signalVaue - measure of  overalll enrichment for the region
8. pValue - statistical significance (-log10)
9. qValue - statistical significance using the FDR (-log10)
10. Point-source called for this peak, 0-based offset from chromo star


## Sources
* http://useast.ensembl.org/info/website/upload/bed.html
* https://hbctraining.github.io/Intro-to-ChIPseq-flipped/lessons/07_handling_peaks_bedtools.html
