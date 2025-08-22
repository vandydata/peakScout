import json
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import boto3
import tarfile
import zstandard

# Lana's s3 copy code is at https://github.com/vandydata/peakScout/commit/d9f0a8046b5a84db78a00296eaf068ee54daf037
# 
# 
def extract_zst(archive: Path, out_path: Path):
    """extract .zst file
    works on Windows, Linux, MacOS, etc.
    
    Parameters
    ----------
    archive: pathlib.Path or str
      .zst file to extract
    out_path: pathlib.Path or str
      directory to extract files and directories to
    """
    
    if zstandard is None:
        raise ImportError("pip install zstandard")
    archive = Path(archive).expanduser()
    out_path = Path(out_path).expanduser().resolve()
    # need .resolve() in case intermediate relative dir doesn't exist
    dctx = zstandard.ZstdDecompressor()
    with tempfile.TemporaryFile(suffix=".tar") as ofh:
        with archive.open("rb") as ifh:
            dctx.copy_stream(ifh, ofh)
        ofh.seek(0)
        with tarfile.open(fileobj=ofh) as z:
            z.extractall(out_path)

def download_and_extract_reference(species, bucket_name='cds-peakscout-public'):
    """
    Download and extract reference data for a given species from S3
    
    Parameters
    ----------
    species: str
        Species identifier (e.g., 'mm10', 'hg38', 'mm39')
    bucket_name: str
        S3 bucket containing reference files
        
    Returns
    -------
    str: Path to extracted reference directory
    """
    
    # Map species to S3 file names
    species_mapping = {
        'mm10': 'mouse_mm10.tar.zst',
        'mm39': 'mouse_mm39.tar.zst', 
        'hg19': 'human_hg19.tar.zst',
        'hg38': 'human_hg38.tar.zst',
        'dm6': 'fly_BDGP6.54.tar.zst',
        'ce11': 'worm_WBcel235.tar.zst',
        'danRer11': 'zebrafish_GRCz11.tar.zst',
        'sacCer3': 'yeast_R64-1-1.tar.zst',
        'susScr11': 'pig_Sscrofa11.1.tar.zst',
        'tair10': 'arabidopsis_TAIR10.tar.zst',
        'xenTro10': 'frog_v10.1.tar.zst'
    }
    
    # Check if species is supported
    if species not in species_mapping:
        raise ValueError(f"Unsupported species: {species}. Supported species: {list(species_mapping.keys())}")
    
    file_name = species_mapping[species]
    ref_dir = f'/tmp/{species}'
    archive_path = f'/tmp/{file_name}'
    
    # Check if reference already exists and is valid
    if os.path.exists(ref_dir) and os.listdir(ref_dir):
        print(f"Reference for {species} already exists at {ref_dir}")
        return ref_dir
    
    # Download file from S3
    s3_client = boto3.client('s3')
    try:
        print(f"Downloading {file_name} from S3...")
        s3_client.download_file(bucket_name, file_name, archive_path)
        print(f"Downloaded {file_name} to {archive_path}")
    except Exception as e:
        raise Exception(f"Failed to download {file_name} from S3: {str(e)}")
    
    # Extract the archive
    try:
        print(f"Extracting {archive_path} to {ref_dir}...")
        os.makedirs(ref_dir, exist_ok=True)
        extract_zst(archive_path, ref_dir)
        
        # Verify extraction
        if os.path.exists(ref_dir) and os.listdir(ref_dir):
            print(f"Successfully extracted reference to {ref_dir}")
            # Clean up archive file
            os.remove(archive_path)
            return ref_dir
        else:
            raise Exception("Extraction appeared to succeed but directory is empty")
            
    except Exception as e:
        raise Exception(f"Failed to extract {archive_path}: {str(e)}")
# 
# 
def handler(event, context):
    """
    Enhanced Lambda handler for peakScout that uses /tmp for output
    
    Expected input:
    {
        "command": "decompose|peak2gene|gene2peak",
        "args": ["--species", "hg38", "--k", "5", ...],
        "return_files": true,  # Optional: whether to return file contents
        "max_file_size": 1048576  # Optional: max file size to return (1MB default)
    }
    """
    try:
        command = event.get('command')
        args = event.get('args', [])
        return_files = event.get('return_files', True)
        max_file_size_MB = 20
        max_file_size = event.get('max_file_size', (max_file_size_MB * 1048576))  # 1MB default
        s3_bucket = event.get('s3_bucket', 'cds-peakscout-public')

        if not command:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No command specified'})
            }
        
        # Extract species from args to download reference data
        species = None
        for i, arg in enumerate(args):
            if arg == '--species' and i + 1 < len(args):
                species = args[i + 1]
                break
        
        # Download and extract reference data
        ref_dir = None
        if species and species != 'test':  # Skip download for test species
            try:
                ref_dir = download_and_extract_reference(species, s3_bucket)
                print(f"Reference data ready at: {ref_dir}")
            except Exception as e:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': f'Failed to setup reference data for species {species}: {str(e)}',
                        'error_type': 'ReferenceDataError'
                    })
                }
        
        
        # Create temporary output directory in /tmp
        temp_output_dir = tempfile.mkdtemp(prefix='peakscout_output_', dir='/tmp')
        
        # Simple approach: Replace output path in args
        modified_args = []
        skip_next = False
        
        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue
                
            if arg in ['--o', '--out_dir', '--out']:
                # Add the flag and redirect to temp directory
                modified_args.append(arg)
                modified_args.append(temp_output_dir)
                # Skip the next argument (original output path)
                skip_next = True
            else:
                # Keep all other arguments as-is
                modified_args.append(arg)
        
        # Build the peakScout command - command goes at the END as a positional argument
        cmd = ['python3', 'peakScout'] + modified_args + [command]
        
        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd='/var/task'
        )
        
        # Prepare response
        response_data = {
            'command': ' '.join(cmd),
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'temp_output_dir': temp_output_dir,
            'species': species,
            'ref_dir_used': ref_dir
        }
        
        # If successful and return_files is enabled, collect output files
        if result.returncode == 0 and return_files:
            output_files = {}
            
            output_path = Path(temp_output_dir)
            if output_path.exists():
                # Collect all files in output directory
                for file_path in output_path.rglob('*'):
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            relative_path = str(file_path.relative_to(output_path))
                            
                            if file_size <= max_file_size:
                                # Read file content
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    output_files[relative_path] = {
                                        'content': content,
                                        'size': file_size,
                                        'type': 'text',
                                        'full_path': str(file_path)
                                    }
                                except UnicodeDecodeError:
                                    # Binary file, encode as base64
                                    import base64
                                    with open(file_path, 'rb') as f:
                                        content = base64.b64encode(f.read()).decode('utf-8')
                                    output_files[relative_path] = {
                                        'content': content,
                                        'size': file_size,
                                        'type': 'binary_base64',
                                        'full_path': str(file_path)
                                    }
                            else:
                                # File too large, just include metadata
                                output_files[relative_path] = {
                                    'content': f'<FILE_TOO_LARGE: {file_size} bytes>',
                                    'size': file_size,
                                    'type': 'metadata_only',
                                    'full_path': str(file_path)
                                }
                        except Exception as e:
                            output_files[relative_path] = {
                                'content': f'<ERROR_READING_FILE: {str(e)}>',
                                'size': 0,
                                'type': 'error',
                                'full_path': str(file_path) if 'file_path' in locals() else 'unknown'
                            }
            
            response_data['output_files'] = output_files
            response_data['files_found'] = len(output_files)
        
        # Clean up temp directory (but keep reference data for reuse)
        try:
            shutil.rmtree(temp_output_dir)
            response_data['cleanup_status'] = 'success'
        except Exception as e:
            response_data['cleanup_status'] = f'failed: {str(e)}'
        
        return {
            'statusCode': 200 if result.returncode == 0 else 500,
            'body': json.dumps(response_data, indent=2)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'error_type': type(e).__name__
            })
        }

def list_tmp_contents():
    """Helper function to list /tmp contents for debugging"""
    try:
        tmp_path = Path('/tmp')
        contents = []
        for item in tmp_path.iterdir():
            if item.is_file():
                contents.append(f"FILE: {item} ({item.stat().st_size} bytes)")
            elif item.is_dir():
                file_count = len(list(item.rglob('*')))
                contents.append(f"DIR:  {item}/ ({file_count} items)")
        return "\n".join(contents) if contents else "No items in /tmp"
    except Exception as e:
        return f"Error listing /tmp: {str(e)}"