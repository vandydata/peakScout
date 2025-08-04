#!/bin/bash
# Script to download GTF files for common organisms and run peakScout decompose
#
# - Download GTF files for common organisms
# - Decompress the GTF files
# - Run peakScout decompose for each species
# - Compress the decomposed files into tar.zst format
# - Upload the compressed files to a public S3 bucket
# 

set -euo pipefail

declare -A gtf_urls=(
    ["arabidopsis_TAIR10"]="https://ftp.ebi.ac.uk/ensemblgenomes/pub/plants/current/gtf/arabidopsis_thaliana/Arabidopsis_thaliana.TAIR10.61.gtf.gz"
    ["worm_WBcel235"]="https://ftp.ebi.ac.uk/ensemblgenomes/pub/metazoa/current/gtf/caenorhabditis_elegans/Caenorhabditis_elegans.WBcel235.61.gtf.gz"
    ["fly_BDGP6.54"]="https://ftp.ensembl.org/pub/release-114/gtf/drosophila_melanogaster/Drosophila_melanogaster.BDGP6.54.114.gtf.gz"
    ["zebrafish_GRCz11"]="https://ftp.ensembl.org/pub/current_gtf/danio_rerio/Danio_rerio.GRCz11.114.gtf.gz"
    ["yeast_R64-1-1"]="https://ftp.ebi.ac.uk/ensemblgenomes/pub/fungi/current/gtf/saccharomyces_cerevisiae/Saccharomyces_cerevisiae.R64-1-1.61.gtf.gz"
    ["frog_v10.1"]="https://ftp.ensembl.org/pub/current_gtf/xenopus_tropicalis/Xenopus_tropicalis.UCB_Xtro_10.0.114.gtf.gz"
    ["mouse_mm39"]="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M37/gencode.vM37.basic.annotation.gtf.gz"
    ["mouse_mm10"]="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M25/gencode.vM25.basic.annotation.gtf.gz"
    ["human_hg38"]="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_48/gencode.v48.basic.annotation.gtf.gz"
    ["human_hg19"]="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_10/gencode.v10.annotation.gtf.gz"
    ["pig_Sscrofa11.1"]="https://ftp.ensembl.org/pub/release-114/gtf/sus_scrofa/Sus_scrofa.Sscrofa11.1.114.gtf.gz"
)

# Define the order explicitly
species_order=(
    "arabidopsis_TAIR10"
    "worm_WBcel235" 
    "fly_BDGP6.54"
    "zebrafish_GRCz11"
    "yeast_R64-1-1"
    "frog_v10.1"
    "mouse_mm39"
    "mouse_mm10"
    "human_hg38"
    "human_hg19"
    "pig_Sscrofa11.1"
)



GTF_DIR="reference/gtf_files"
mkdir -p $GTF_DIR

for species in "${species_order[@]}"; do
    url="${gtf_urls[$species]}"
    
    filename=$(basename "$url")
    
    echo "Downloading $species: $filename..."
    wget -q -O "${GTF_DIR}/${filename}" "$url"
    
    gunzip -f "${GTF_DIR}/${filename}"
    
    decompressed_filename="${filename%.gz}"
    echo "Saved ${GTF_DIR}/${decompressed_filename}"

    # peakScout decompose
    ./src/peakScout decompose --ref_dir reference --species ${species} --gtf_ref ${GTF_DIR}/${decompressed_filename}

    # tar.zst
    tar -cf - reference/${species} | zstd > reference/${species}.tar.zst

    # Copy to public S3 bucket for this project
    aws s3 cp reference/${species}.tar.zst s3://cds-peakscout-public/
    
done

