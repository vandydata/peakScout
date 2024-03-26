# MACS2 BED files

MACS2 generates several outputs, but we focus on:
* sample.macs2_peaks.narrowPeak.bed
* sample.macs2_peak.xls

## sample.macs2_peaks.narrowPeak.bed

Coordinates are 0-based.

1. chrom – Name of the chromosome (or contig, scaffold, etc.).
2. chromStart – The starting position of the feature in the chromosome or scaffold. The first base in a chromosome is numbered 0.
3. chromEnd – The ending position of the feature in the chromosome or scaffold. The chromEnd base is not included in the display of the feature. For example, the first 100 bases of a chromosome are defined aschromStart=0, chromEnd=100, and span the bases numbered 0-99.
4. name – Name was given to a region (preferably unique). Use ‘.’ if no name is assigned. Defines the name of the BED line. This label is displayed to the left of the BED line in the Genome Browser window when the track is open to full display mode or directly to the left of the item in pack mode.
5. score – Indicates how dark the peak will be displayed in the browser (0-1000). If all scores were ‘0’ when the data were submitted to the DCC, the DCC assigned scores 1-1000 based on signal value. Ideally, the average signalValue per base spread is between 100-1000. Integer score for display calculated as int(-10*log10qvalue). Please note that currently, this value might be out of the [0-1000] range defined in UCSC Encode narrowPeak format. If the track line useScore attribute is set to 1 for this annotation data set, the score value will determine the level of gray in which this feature is displayed (higher numbers = darker gray).
6. strand – +/- to denote strand or orientation (whenever applicable). Use ‘.’ if no orientation is assigned.
7. signalValue – Measurement of overall (usually, average) enrichment for the region. fold-change.
8. pValue – Measurement of statistical significance (-log10). Use -1 if no p-Value is assigned. -log10pvalue.
9. qValue – Measurement of statistical significance using false discovery rate (-log10). Use -1 if no q-Value is assigned. -log10qvalue.
10. peak – Point-source called for this peak; 0-based offset from chromStart. Use -1 if no point-source called. Relative summit position to peak start.

Example:

```
1	3670300	3672528	Ctrl_H3K4me3-1_R1.macs2_peak_1	1158	.	48.564	119.41	115.826	526
1	4785153	4786185	Ctrl_H3K4me3-1_R1.macs2_peak_2	722	.	28.0169	75.2785	72.2012	348
1	4807440	4808656	Ctrl_H3K4me3-1_R1.macs2_peak_3	722	.	28.1581	75.2785	72.2012	563
1	4857304	4858793	Ctrl_H3K4me3-1_R1.macs2_peak_4	989	.	35.7781	102.358	98.9791	737
1	5018595	5020583	Ctrl_H3K4me3-1_R1.macs2_peak_5	315	.	17.8932	34.194	31.5385	946
1	5082896	5083698	Ctrl_H3K4me3-1_R1.macs2_peak_6	727	.	33.6272	75.7986	72.7163	538
1	6213861	6215701	Ctrl_H3K4me3-1_R1.macs2_peak_7	1256	.	50.1443	129.373	125.661	531
1	6729389	6730579	Ctrl_H3K4me3-1_R1.macs2_peak_8	226	.	13.6456	25.2131	22.6585	707
1	6730828	6731357	Ctrl_H3K4me3-1_R1.macs2_peak_9	151	.	10.4656	17.5879	15.1239	390
1	6733737	6734191	Ctrl_H3K4me3-1_R1.macs2_peak_10	75	.	6.74013	9.86549	7.52832	293
```


## sample.macs2_peak.xls

Coordinates in XLS are 1-based.

This is a tabular file which contains information about called peaks. You can open it in excel and sort/filter using excel functions. Information includes:
1. chrom
2. chromStart
3. chromEnd
4. length of the peak region
5. absolute peak summit position 
6. pileup height at peak summit, -log10(p-value) for the peak summit (e.g. p-value =1e-10, then this value should be 10)
7. fold enrichment for this peak summit against random Poisson distribution with local lambda, -log10(q-value) at peak summit
8

5, 6, and 7 are unique, however:

5. `abs_summit` can be calculated in narrowPeak.bed by `chromStart + peak`
6. 
