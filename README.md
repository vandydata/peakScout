# peakScout

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/vandydata/peakScout.git
cd peakScout
```

### 2. Make the Script Executable
```bash
chmod +x peakScout
```

### 3. Add to Path
```bash
export PATH="$PATH:$(pwd)"
```

Alternatively, add this line to ~/.bashrc to make this change permanent

### 4. Set Up Virtual Environment
```bash
python3 -m venv peakscout
source peakscout/bin/activate
pip3 install -r requirements.txt
```

## Usage

### Decomposing Reference GTF
To decompose a reference GTF file so that it can be used by peakScout, run the following command
```bash
peakScout decompose --ref_dir /path/to/where/outputs/stored --species species of gtf --gtf_ref /path/to/gtf/file
```

### Finding Nearest Genes
Once a reference GTF has been decomposed, you can use the decomposition to find the nearest genes to your peaks. Peak files can be MACS2 or SEACR outputs and can be Excel sheets or BED files.

Run the following command to create an Excel sheet containing the nearest k genes to your peaks
```bash
peakScout peak2gene --peak_file /path/to/peak/file --peak_type MACS2/SEACR --species species of gtf --k number of nearest peaks --ref_dir /path/to/reference/directory --output_name name of output file --o /path/to/save/output --output_type csv/xslx
```

## Notes

Genomes to target: mm10, mm39, hg19, hg38

Get annotations from Gencode, i.e. M25 for mm10 (which is aka GRCm38)

From gencode files, we can get chr, start, end, feature name, feature type (`gene`, `transcript`, etc), and biotype (eg. `gene_type "TEC";`)

Write a parser for the GTF data and at least get it into the lowest common denominator currently need, optimizations can come later

