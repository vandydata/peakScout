# 2. Functions

## 2.1 Overview

PeakScout provides a comprehensive suite of functions for mapping genomic peaks to genes and vice versa, enabling researchers to quickly interpret ChIP-seq and similar experimental data without extensive bioinformatics expertise. The tool's functionality is organized into modular components that handle different aspects of the analysis workflow, from input processing to output generation.

## 2.2 Language and algorithmic approach

PeakScout is implemented in Python, leveraging the high-performance Polars data processing library for efficient manipulation of genomic data. This choice of technology enables rapid processing of large genomic datasets while maintaining a user-friendly interface. The core algorithmic approach in PeakScout centers around efficient chromosome-specific feature decomposition and nearest-feature detection.

For reference data management, PeakScout employs a hierarchical decomposition strategy that organizes genomic features by type (gene, exon, CDS, etc.) and chromosome. This approach, implemented in `decompose_ref.py`, significantly reduces the search space when identifying nearest features, as only features on the same chromosome need to be considered. Each feature collection is further organized into separate files sorted by start and end positions, enabling efficient binary search operations when determining proximity relationships.

The nearest-feature detection algorithm, implemented in `process_features.py`, employs a bidirectional search strategy that simultaneously evaluates upstream and downstream features relative to each genomic peak. This approach is particularly efficient as it leverages the pre-sorted nature of the decomposed reference data. As illustrated in Figure 1, PeakScout's approach allows for rapid identification of nearest features even for datasets containing thousands of peaks and reference features.

## 2.3 Supported operations

Table 1 illustrates the primary operations supported by PeakScout. The tool provides two main analytical pathways: peak-to-gene mapping and gene-to-peak mapping, each with flexible parameter options to accommodate different research questions.

**Table 1. Primary operations supported by PeakScout**

| Operation | Function | Description |
|-----------|----------|-------------|
| Reference decomposition | `decompose_gtf()` | Decomposes GTF reference files into chromosome-specific feature collections |
| Peak processing | `process_peaks()` | Processes peak files from MACS2, SEACR, or BED format into standardized internal representation |
| Gene processing | `process_genes()` | Processes gene lists for gene-to-peak mapping |
| Peak-to-gene mapping | `peak2gene()` | Maps genomic peaks to their nearest genes |
| Gene-to-peak mapping | `gene2peak()` | Maps genes to their nearest genomic peaks |
| Nearest feature detection | `get_nearest_features()` | Core algorithm for identifying nearest genomic features |
| Output generation | `write_to_csv()`, `write_to_excel()` | Formats and writes results to researcher-friendly output formats |

The `peak2gene` function provides comprehensive options for defining peak boundaries and proximity constraints. Users can choose between native peak boundaries (as defined by the peak caller), peak summits, or artificial boundaries with user-defined extensions. Additionally, users can specify maximum distance constraints for upstream and downstream features, ensuring that only biologically relevant associations are reported.

For input flexibility, PeakScout supports multiple peak file formats through specialized processing functions. The `process_peaks` function automatically detects and handles MACS2 output (both Excel and BED formats) and SEACR output, standardizing these diverse formats into a consistent internal representation. This enables seamless integration with various peak calling workflows without requiring users to perform format conversions.

The following examples illustrate the use of PeakScout's functions:

```python
# Example 1: Peak-to-gene mapping with MACS2 peaks
peak2gene("peaks.bed", "MACS2", "mm10", 3, "reference/", "output", "results", "xlsx")

# Example 2: Gene-to-peak mapping with custom distance constraints
peak2gene("peaks.bed", "MACS2", "mm10", 3, "reference/", "output", "results", "xlsx", 
          up_bound=5000, down_bound=1000)

# Example 3: Finding peaks associated with a specific gene list
gene2peak("peaks.bed", "MACS2", "gene_list.csv", "mm10", 5, "reference/", "output", "results", "csv")
```

## 2.4 Feature detection and proximity analysis

The core of PeakScout's analytical capability lies in its feature detection and proximity analysis algorithms. Unlike some tools that simply report the nearest TSS for each peak, PeakScout implements a more sophisticated approach that considers the full genomic context.

The `get_nearest_features` function in `process_features.py` employs a bidirectional search strategy that simultaneously evaluates upstream and downstream features. This approach allows PeakScout to identify the k-nearest features in both directions, providing a more comprehensive view of the genomic neighborhood around each peak. The function also handles feature overlaps, ensuring that genes directly overlapping with peaks are prioritized in the results.

For proximity constraints, PeakScout allows users to specify maximum distance thresholds for upstream and downstream features through the `up_bound` and `down_bound` parameters. This functionality enables researchers to focus on biologically relevant associations based on their understanding of regulatory element behavior in their specific experimental context.

The `constrain_features` function further optimizes the search process by filtering reference features based on these distance constraints before performing the detailed proximity analysis. This pre-filtering step significantly reduces the computational burden for large datasets, enabling rapid analysis even on standard desktop computers.

## 2.5 Output generation and visualization

PeakScout provides flexible output options through its `write_output.py` module. Results can be exported in both CSV and Excel formats, with the Excel output including additional formatting for improved readability. The Excel output features alternating row colors, column width optimization, and pre-configured filters for chromosome selection, making it immediately usable for downstream analysis and interpretation.

The output includes comprehensive information about each peak or gene, including:
- Genomic coordinates (chromosome, start, end)
- Feature identifiers (peak name or gene name)
- The k-nearest features (as specified by the user)
- Distance to each nearest feature (with negative values indicating upstream features)

This rich output format enables researchers to quickly identify potential regulatory relationships and prioritize candidates for further experimental validation.
