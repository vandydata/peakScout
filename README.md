# peakScout <a href="https://github.com/vandydata/peakScout"><img src="assets/logo.svg" align="right" height="350"  alt="peakScout website"/></a>

<!-- badges: start -->
[![peakScout](https://github.com/vandydata/peakScout/actions/workflows/python.yaml/badge.svg)](https://github.com/vandydata/peakScout/actions/workflows/python.yaml)
[![License: AGPLv3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
<!-- badges: end -->

peakScout is a user-friendly and reversible peak-to-gene translator for genomic peak calling results

> Please cite CITATION if you use peakScout, thank you!

## Overview

PeakScout is a bioinformatics tool designed to bridge the gap between genomic peak data and gene annotations, enabling researchers to understand the relationship between regulatory elements and their target genes. At its core, peakScout processes genomic peak files from common peak callers like MACS2 and SEACR and maps them to nearby genes using reference genome annotations. The workflow begins with input processing, where peak files are standardized and reference GTF files are decomposed into chromosome-specific feature collections. The core analysis modules then perform bidirectional mapping: peak-to-gene identifies which genes are potentially regulated by specific genomic regions, while gene-to-peak reveals which regulatory elements might influence particular genes. Throughout this process, nearest-feature detection algorithms handle the complex spatial relationships between genomic elements, considering factors like distance constraints and feature overlaps. Finally, the results are formatted into researcher-friendly CSV and Excel outputs, providing a comprehensive view of the genomic landscape that connects regulatory elements to their potential gene targets.

## Installation

These instructions should generally work without modification in linux-based environments. If you are using Windows, we strongly recommend you use WSL2 to have a Linux environment within Windows.

### 1. Clone the Repository

```bash
git clone https://github.com/vandydata/peakScout.git
cd peakScout
```

### 2. Make the Script Executable
```bash
chmod +x src/peakScout
```

### 3. Add to Path
```bash
export PATH="$PATH:$(pwd)/src"
```

Alternatively, edit your `~/.bashrc` to make this change permanent, but be sure to include the complete path in the file itself, not the `$(pwd)`. 

### 4. Set Up Virtual Environment

Using `venv`

```bash
# in peakScount main directory
python3 -m venv peakscout
source peakscout/bin/activate
pip3 install -r requirements.txt
```

Or using `uv`
```bash
# in peakScount main directory
uv venv peakscout
source peakscout/bin/activate
uv pip install -r requirements.txt
```

## Usage

### Decomposing Reference GTF
To decompose a reference GTF file so that it can be used by peakScout, run the following command
```bash
peakScout decompose --ref_dir /path/to/where/outputs/stored --species species of gtf --gtf_ref /path/to/gtf/file
```

Specific example:

```bash
peakScout decompose \
--ref_dir reference/ \
--species mm39 \
--gtf_ref reference/gencode.vM37.basic.annotation.gtf
```

A directory called `reference/mm39` will be created and you will use the `mm39` as the species name in other peakScout operations.

### Finding Nearest Genes

Once a reference GTF has been decomposed, you can use the decomposition to find the nearest genes to your peaks. Peak files can be MACS2, SEACR outputs, or standard BED6 format files and can be Excel sheets or BED files.

Run the following command to create an Excel sheet containing the nearest k genes to your peaks
```bash
peakScout peak2gene --peak_file /path/to/peak/file --peak_type MACS2/SEACR/BED6 --species species of gtf --k number of nearest genes --ref_dir /path/to/reference/directory --output_name name of output file --o /path/to/save/output --output_type csv/xslx
```

Specific example:

```bash
peakScout peak2gene \
--peak_file test/test_MACS2.bed \
--peak_type MACS2 \
--species mm39 \
--k 2 \
--ref_dir reference/mm39 \
--output_name peakScout_test_MACS2 \
--o my_output_dir \
--output_type xslx
```

Specific example:

```bash
peakScout peak2gene \
--peak_file test/test_MACS2.bed \
--peak_type MACS2 \
--species mm39 \
--k 2 \
--ref_dir reference/mm39 \
--output_name peakScout_test_MACS2 \
--o my_output_dir \
--output_type xslx
```

### Finding Nearest Peaks

Once a reference GTF has been decomposed, you can use the decomposition to find the nearest peaks to a set of genes. Peak files can be MACS2, SEACR outputs, or standard BED6 format files and can be Excel sheets or BED files. Gene names should be in a single column CSV file with no header.

Run the following command to create an Excel sheet containing the nearest k peaks to your genes
```bash
peakScout gene2peak --peak_file /path/to/peak/file --peak_type MACS2/SEACR/BED6 --gene_file /path/to/gene/file --species species of gtf --k number of nearest peaks --ref_dir /path/to/reference/directory --output_name name of output file --o /path/to/save/output --output_type csv/xslx
```

Specific example:
```bash
peakScout gene2peak --peak_file /path/to/peak/file --peak_type MACS2/SEACR/BED6 --gene_file /path/to/gene/file --species species of gtf --k number of nearest peaks --ref_dir /path/to/reference/directory --output_name name of output file --o /path/to/save/output --output_type csv/xslx
```

## Decomposed references for common organisms

For your convenience, we have prepared decomposed GTF files for common organisms, generated by `src/utils/decompose-common-organisms.sh` from the following GTF files:

* `arabidopsis_TAIR10` - https://ftp.ebi.ac.uk/ensemblgenomes/pub/plants/current/gtf/arabidopsis_thaliana/Arabidopsis_thaliana.TAIR10.61.gtf.gz
* `fly_BDGP6.54` - https://ftp.ensembl.org/pub/current_gtf/drosophila_melanogaster/Drosophila_melanogaster.BDGP6.32.114.gtf.gz
* `frog_v10.1` - https://ftp.ensembl.org/pub/current_gtf/xenopus_tropicalis/Xenopus_tropicalis.UCB_Xtro_10.0.114.gtf.gz
* `human_hg38` - https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_48/gencode.v48.basic.annotation.gtf.gz
* `human_hg19` - https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_10/gencode.v10.annotation.gtf.gz
* `mouse_mm39` - https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M37/gencode.vM37.basic.annotation.gtf.gz
* `mouse_mm10` - https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M25/gencode.vM25.basic.annotation.gtf.gz
* `pig_Sscrofa11.1` - https://ftp.ensembl.org/pub/release-114/gtf/sus_scrofa/Sus_scrofa.Sscrofa11.1.114.gtf.gz
* `worm_WBcel235` - https://ftp.ebi.ac.uk/ensemblgenomes/pub/metazoa/current/gtf/caenorhabditis_elegans/Caenorhabditis_elegans.WBcel235.61.gtf.gz
* `yeast_R64-1-1` - https://ftp.ebi.ac.uk/ensemblgenomes/pub/fungi/current/gtf/saccharomyces_cerevisiae/Saccharomyces_cerevisiae.R64-1-1.61.gtf.gz
* `zebrafish_GRCz11` - https://ftp.ensembl.org/pub/current_gtf/danio_rerio/Danio_rerio.GRCz11.114.gtf.gz

You can download these from a publix AWS S3 bucket as ZSTD-compressed files, which can be decompressed with `zstd -d`:

* `s3://peakscout/common-organisms/arabidopsis_TAIR10.zst`
* `s3://peakscout/common-organisms/worm_WBcel235.zst`
* etc...


## FAQ

### What is WSL2 and how do I install it?

Start at https://learn.microsoft.com/en-us/windows/wsl/install and then Google for your issues. We cannot provide support for this. 

### How to get a GTF file?

Ensembl and Gencode have them. For example, go to https://www.gencodegenes.org/mouse/release_M37.html and select the GTF you'd like to decompose, then:
```
mkdir reference
cd reference
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M37/gencode.vM37.basic.annotation.gtf.gz
gunzip gencode.vM37.basic.annotation.gtf.gz
```


## Notes

Genomes to target: mm10, mm39, hg19, hg38

Get annotations from Gencode, i.e. M25 for mm10 (which is aka GRCm38)

From gencode files, we can get chr, start, end, feature name, feature type (`gene`, `transcript`, etc), and biotype (eg. `gene_type "TEC";`)

Write a parser for the GTF data and at least get it into the lowest common denominator currently need, optimizations can come later

