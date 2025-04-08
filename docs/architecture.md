# PeakScout Architecture

PeakScout is a bioinformatics tool designed to bridge the gap between genomic peak data and gene annotations, enabling researchers to understand the relationship between regulatory elements and their target genes. At its core, PeakScout processes genomic peak files from common peak callers like MACS2 and SEACR, and maps them to nearby genes using reference genome annotations. The workflow begins with input processing, where peak files are standardized and reference GTF files are decomposed into chromosome-specific feature collections. The core analysis modules then perform bidirectional mapping: peak-to-gene identifies which genes are potentially regulated by specific genomic regions, while gene-to-peak reveals which regulatory elements might influence particular genes. Throughout this process, sophisticated nearest-feature detection algorithms handle the complex spatial relationships between genomic elements, considering factors like distance constraints and feature overlaps. Finally, the results are formatted into researcher-friendly CSV and Excel outputs, providing a comprehensive view of the genomic landscape that connects regulatory elements to their potential gene targets.

## Component Relationships

```mermaid
graph TD
    %% Main modules
    decompose[decompose_ref.py] --> peak2gene[peak2gene.py]
    decompose --> gene2peak[gene2peak.py]
    
    %% Supporting modules
    process_input[process_input.py] --> peak2gene
    process_input --> gene2peak
    process_features[process_features.py] --> peak2gene
    process_features --> gene2peak
    
    %% Output generation
    peak2gene --> write_output[write_output.py]
    gene2peak --> write_output
    
    %% Data flow
    input_files[Input Files<br>MACS2/SEACR/BED] --> process_input
    ref_files[Reference Files<br>GTF] --> decompose
    write_output --> results[Results<br>CSV/Excel]
    
    %% Subcomponents and relationships
    subgraph "Core Analysis"
        peak2gene
        gene2peak
    end
    
    subgraph "Data Processing"
        process_input
        process_features
        decompose
    end
    
    %% Function relationships
    decompose -. "decompose_gtf()" .-> feature_data[Organized Feature Data]
    process_input -. "process_peaks()" .-> standardized_peaks[Standardized Peak Data]
    process_features -. "find_nearest()" .-> nearest_features[Nearest Features]
    peak2gene -. "find_nearest()" .-> peak_to_gene_mapping[Peak→Gene Mapping]
    gene2peak -. "find_nearest()" .-> gene_to_peak_mapping[Gene→Peak Mapping]
    
    %% Style
    classDef core fill:#f9f,stroke:#333,stroke-width:2px;
    classDef support fill:#bbf,stroke:#333,stroke-width:1px;
    classDef data fill:#bfb,stroke:#333,stroke-width:1px;
    
    class peak2gene,gene2peak core;
    class process_input,process_features,decompose,write_output support;
    class input_files,ref_files,results,feature_data,standardized_peaks,nearest_features data;
```

## Data Flow

1. **Input Processing**:
   - Peak files (MACS2, SEACR, BED) are processed by `process_input.py`
   - Reference GTF files are decomposed by `decompose_ref.py`

2. **Core Analysis**:
   - `peak2gene.py` maps peaks to nearby genes
   - `gene2peak.py` maps genes to nearby peaks
   - Both rely on feature processing functions from `process_features.py`

3. **Output Generation**:
   - Results are formatted and written to CSV/Excel by `write_output.py`

## Module Dependencies

- **Core Modules**: `peak2gene.py`, `gene2peak.py`
- **Supporting Modules**: `process_input.py`, `process_features.py`, `decompose_ref.py`, `write_output.py`
- **External Dependencies**: Polars, Pandas, NumPy
