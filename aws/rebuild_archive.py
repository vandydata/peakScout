#!/usr/bin/env python3
"""
Rebuild a peakScout species archive, adding a CRE BED file

Usage: python3 rebuild_archive.py <species_key> <s3_archive_name> <internal_dir> <cre_bed_src>
"""
import sys, os, tarfile, zstandard, tempfile, shutil, boto3
from pathlib import Path

species_key   = sys.argv[1]   # e.g. hg38
s3_name       = sys.argv[2]   # e.g. human_hg38.tar.zst
internal_dir  = sys.argv[3]   # e.g. reference/human_hg38
cre_src       = sys.argv[4]   # path to local CRE BED file

bucket = 'cds-peakscout-public'
workdir = Path(f'/tmp/rebuild_{species_key}')
workdir.mkdir(exist_ok=True)

archive_path = workdir / s3_name
extract_dir  = workdir / 'extracted'
extract_dir.mkdir(exist_ok=True)
out_archive  = workdir / s3_name  # overwrite same name

print(f"[{species_key}] Downloading {s3_name}...")
s3 = boto3.client('s3')
s3.download_file(bucket, s3_name, str(archive_path))
print(f"[{species_key}] Downloaded ({archive_path.stat().st_size / 1e6:.1f} MB)")

print(f"[{species_key}] Extracting...")
dctx = zstandard.ZstdDecompressor()
with tempfile.TemporaryFile(suffix=".tar") as ofh:
    with archive_path.open("rb") as ifh:
        dctx.copy_stream(ifh, ofh)
    ofh.seek(0)
    with tarfile.open(fileobj=ofh) as tf:
        tf.extractall(extract_dir)
archive_path.unlink()  # free space
print(f"[{species_key}] Extracted")

# add CRE file
cre_dest = extract_dir / internal_dir / 'cre' / Path(cre_src).name
cre_dest.parent.mkdir(parents=True, exist_ok=True)
print(f"[{species_key}] Copying CRE ({Path(cre_src).stat().st_size / 1e6:.1f} MB)...")
shutil.copy2(cre_src, cre_dest)
print(f"[{species_key}] CRE copied to {cre_dest}")

# recompress
print(f"[{species_key}] Compressing...")
cctx = zstandard.ZstdCompressor(level=3, threads=-1)
with tempfile.TemporaryFile(suffix=".tar") as tar_fh:
    with tarfile.open(fileobj=tar_fh, mode='w') as tf:
        tf.add(extract_dir / internal_dir, arcname=internal_dir)
    tar_fh.seek(0)
    with open(str(out_archive), 'wb') as ofh:
        cctx.copy_stream(tar_fh, ofh)

size_mb = out_archive.stat().st_size / 1e6
print(f"[{species_key}] Compressed archive: {size_mb:.1f} MB")

# upload
print(f"[{species_key}] Uploading to s3://{bucket}/{s3_name}...")
s3.upload_file(str(out_archive), bucket, s3_name)
print(f"[{species_key}] Done.")
