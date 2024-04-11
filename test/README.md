# Test files

## Test file - gene annotation

1. Download https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M25/gencode.vM25.chr_patch_hapl_scaff.basic.annotation.gtf.gz
2. Gunzip file
3. Created a subset of  `gencode.vM25.basic.annotation.gtf` that contains a few genes from chr1 and chr2, and saved to `test.gtf`

## Test file - Peak caller BED files

* `test_MACS2.bed` MACS2 (narrowPeak) file
* `test_SEACR.bed` SEACR file

## Expected test results

See `test_MACS2_expected_results.csv` or as shown below.

For each of the `test_*.bed` files, the finding of nearest genes should be as follows:

| name | closest_gene_name_1   | closest_gene_name_2  | closest_gene_name_3   |
| ------------ | ------- | ------- | ------- |
| peak1        | Rp1     | Gm37483 | Gm6101  |
| peak2        | Gm7182  | Gm37567 | Atp6v1h |
| peak3        | Gm18984 | Gm26901 | Gm19002 |
| peak4        | Sntg1   | Gm38024 | Gm16284 |
| peak5        | Cpa6    | Gm15604 | Gm25253 |
| peak6        | Olah    | Gm37525 | Acbd7   |
| peak7        | Camk1d  | Gm13216 | Cdc123  |
| peak8        | Celf2   | Gm24340 | Gm28641 |
| peak9        | Gm24534 | Gm13254 | Gm13255 |
| peak10       | Gm26478 | Gm13297 | Gm13294 |

