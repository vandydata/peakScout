import json
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import boto3
import tarfile
import zstandard
import gzip
import base64

def extract_zst(archive: Path, out_path: Path):
    """
    extract .zst file
    
    Parameters
    ----------
    archive:    pathlib.Path or str
                .zst file to extract
    out_path:   pathlib.Path or str
                directory to extract files and directories to
      
    """
    
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
    species:     str
                 Species identifier (e.g., 'mm10', 'hg38', 'mm39')
    bucket_name: str
                 S3 bucket containing reference files
        
    Returns
    -------
    str:         Path to extracted reference directory
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
    if os.path.exists(ref_dir):
        expected_species_dir = os.path.join(ref_dir, species)
        if os.path.exists(expected_species_dir):
            gene_dir = os.path.join(expected_species_dir, 'gene')
            if os.path.exists(gene_dir) and os.listdir(gene_dir):
                print(f"Reference for {species} already exists at {ref_dir}")
                return ref_dir
    
    # Download reference file from S3
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
        
        # peakScout expects: ref_dir/{species}/gene/
        # But archives extract to: ref_dir/reference/{species_full_name}/gene/
        # We need to create a symlink or move the directory structure
        
        expected_species_dir = os.path.join(ref_dir, species)
        
        # Find the actual extracted directory
        extracted_ref_dir = None
        for root, dirs, files in os.walk(ref_dir):
            # Look for  "gene" directory
            if 'gene' in dirs:
                gene_dir = os.path.join(root, 'gene')
                # Verify it has chromosome files
                try:
                    if any(f.startswith('chr') and f.endswith('.csv') for f in os.listdir(gene_dir)):
                        extracted_ref_dir = root
                        break
                except:
                    continue
        
        if extracted_ref_dir:
            # Create a symlink from expected path to actual path
            if not os.path.exists(expected_species_dir):
                os.symlink(extracted_ref_dir, expected_species_dir)
                print(f"Created symlink: {expected_species_dir} -> {extracted_ref_dir}")
            
            # Clean up archive file
            os.remove(archive_path)
            return ref_dir  # Return the base ref_dir, peakScout will append species/gene
        else:
            raise Exception("Could not find gene reference files in expected structure")
            
    except Exception as e:
        raise Exception(f"Failed to extract {archive_path}: {str(e)}")


def list_directory_contents(directory_path, max_depth=2):
    """
    Helper function to list directory contents for debugging
    """
    try:
        dir_path = Path(directory_path)
        if not dir_path.exists():
            return f"Directory {directory_path} does not exist"
        
        contents = []
        contents.append(f"=== Contents of {directory_path} ===")
        
        def list_recursive(path, current_depth=0, prefix=""):
            if current_depth > max_depth:
                return
            try:
                items = sorted(path.iterdir())
                for item in items:
                    if item.is_file():
                        size = item.stat().st_size
                        contents.append(f"{prefix} {item.name} ({size:,} bytes)")
                    elif item.is_dir():
                        file_count = len(list(item.iterdir())) if current_depth < max_depth else "?"
                        contents.append(f"{prefix} {item.name}/ ({file_count} items)")
                        if current_depth < max_depth:
                            list_recursive(item, current_depth + 1, prefix + "  ")
            except PermissionError:
                contents.append(f"{prefix} Permission denied")
            except Exception as e:
                contents.append(f"{prefix} Error: {str(e)}")
        
        list_recursive(dir_path)
        return "\n".join(contents)
    except Exception as e:
        return f"Error listing {directory_path}: {str(e)}"


def list_tmp_contents():
    """
    Helper function to list /tmp contents for debugging
    """
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
    

def compress_content(content):
    """
    Compress content with zstd and encode as base64
    """
    compressor = zstandard.ZstdCompressor(level=3)
    compressed = compressor.compress(content.encode('utf-8'))
    return base64.b64encode(compressed).decode('utf-8')


def get_preview(content, preview_lines=5):
    """
    Get first N lines of content as preview
    """
    lines = content.split('\n')
    return '\n'.join(lines[:preview_lines])
    
    
def handler(event, context):
    """
    Lambda handler for peakScout - direct file uploads up to 5MB
    
    Expected input:
    {
        "command": "decompose|peak2gene|gene2peak",
        "args": ["--species", "hg38", "--k", "5", ...],
        "input_files": {
            "peaks.bed": "chr1\t1000\t2000\n..."
        },
        "return_files": true,
        "s3_bucket": "cds-peakscout-public"
    }
    """
    try:
        command = event.get('command')
        args = event.get('args', [])
        input_files = event.get('input_files', {})
        return_files = event.get('return_files', True)
        max_file_size = event.get('max_file_size', 5242880)  # 5MB default
        s3_bucket = event.get('s3_bucket', 'cds-peakscout-public')
        compress_response = event.get('compress_response', True)
        
        if not command:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({'error': 'No command specified'})
            }
        
        # Write uploaded files to /tmp
        for filename, content in input_files.items():
            file_path = f'/tmp/{filename}'
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Wrote uploaded file: {filename} -> {file_path}")
            except Exception as e:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS'
                    },
                    'body': json.dumps({
                        'error': f'Failed to write uploaded file {filename}: {str(e)}',
                        'error_type': 'FileUploadError'
                    })
                }
        
        # Extract species from args to download reference data
        species = None
        for i, arg in enumerate(args):
            if arg == '--species' and i + 1 < len(args):
                species = args[i + 1]
                break
        
        # Download and extract reference data if species is specified
        ref_dir = None
        if species and species != 'test':  # Skip download for test species
            try:
                ref_dir = download_and_extract_reference(species, s3_bucket)
                print(f"Reference data ready at: {ref_dir}")
            except Exception as e:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS'
                    },
                    'body': json.dumps({
                        'error': f'Failed to setup reference data for species {species}: {str(e)}',
                        'error_type': 'ReferenceDataError'
                    })
                }
        
        # Create temporary output directory in /tmp
        temp_output_dir = tempfile.mkdtemp(prefix='peakscout_output_', dir='/tmp')
        
        # Process arguments and replace file paths with /tmp/ paths
        modified_args = []
        skip_next = False
        ref_dir_found = False
        
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
            elif arg == '--ref_dir':
                ref_dir_found = True
                if ref_dir:
                    # Use downloaded reference if we have one
                    modified_args.append(arg)
                    modified_args.append(ref_dir)
                    skip_next = True  # Skip original ref_dir path
                elif species == 'test':
                    # Keep original ref_dir for test species
                    modified_args.append(arg)
                    # Don't skip next - use the provided test reference path
                else:
                    # For real species without downloaded ref, this is an error
                    return {
                        'statusCode': 500,
                        'headers': {
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Headers': 'Content-Type',
                            'Access-Control-Allow-Methods': 'POST, OPTIONS'
                        },
                        'body': json.dumps({
                            'error': f'No reference data available for species {species}. Reference download may have failed.',
                            'error_type': 'ReferenceDataError'
                        })
                    }
            elif arg.startswith('--') and i + 1 < len(args):
                # For file arguments, prepend /tmp/ to the path if file was uploaded
                next_arg = args[i + 1]
                if arg in ['--peak_file', '--gene_file'] and next_arg in input_files:
                    modified_args.append(arg)
                    modified_args.append(f'/tmp/{next_arg}')
                    skip_next = True
                else:
                    modified_args.append(arg)
            else:
                # Keep all other arguments as-is
                modified_args.append(arg)
        
        # Add --ref_dir if it wasn't provided and we have a reference
        if not ref_dir_found and ref_dir:
            modified_args.extend(['--ref_dir', ref_dir])
        
        # Build the peakScout command
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
        
        # Add debug information if requested
        if event.get('debug', False):
            response_data['debug_info'] = {
                'tmp_contents': list_tmp_contents(),
                'ref_dir_contents': list_directory_contents(ref_dir) if ref_dir else "No reference directory"
            }
        
        # If successful and return_files is enabled, return output files with compression
        if result.returncode == 0 and return_files:
            output_files = {}
            
            output_path = Path(temp_output_dir)
            if output_path.exists():
                # Process all output files
                for file_path in output_path.rglob('*'):
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            relative_path = str(file_path.relative_to(output_path))
                            
                            # Check if file is too large (>5MB)
                            if file_size > max_file_size:
                                output_files[relative_path] = {
                                    'size': file_size,
                                    'type': 'file_too_large',
                                    'error': f'File too large ({file_size:,} bytes). Maximum supported: {max_file_size:,} bytes. Please reduce file size and try again.'
                                }
                            else:
                                # Read and compress file content
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    
                                    output_files[relative_path] = {
                                        'content_preview': get_preview(content),
                                        'content': compress_content(content),
                                        'content_compressed': True,
                                        'compression_type': 'zstd',
                                        'size': file_size,
                                        'type': 'text'
                                    }
                                except UnicodeDecodeError:
                                    # Binary file, encode as base64
                                    with open(file_path, 'rb') as f:
                                        binary_content = f.read()
                                    output_files[relative_path] = {
                                        'content': base64.b64encode(binary_content).decode('utf-8'),
                                        'content_compressed': False,
                                        'size': file_size,
                                        'type': 'binary_base64'
                                    }
                        except Exception as e:
                            output_files[relative_path] = {
                                'type': 'processing_error',
                                'error': str(e)
                            }
            
            response_data['output_files'] = output_files
            response_data['files_found'] = len(output_files)
        
        # Clean up
        try:
            shutil.rmtree(temp_output_dir)
            response_data['cleanup_status'] = 'success'
        except Exception as e:
            response_data['cleanup_status'] = f'failed: {str(e)}'
        
        # Prepare response
        status_code = 200 if result.returncode == 0 else 500
        response_body = json.dumps(response_data, indent=2)
        
        # Compress response if it's large or if compression is requested
        if compress_response and len(response_body) > 100000:  # Compress if > 100KB
            try:
                # Compress the JSON
                compressed_data = gzip.compress(response_body.encode('utf-8'))
                encoded_data = base64.b64encode(compressed_data).decode('utf-8')
                
                return {
                    'statusCode': status_code,
                    'headers': {
                        'Content-Encoding': 'gzip',
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS'
                    },
                    'body': encoded_data,
                    'isBase64Encoded': True,
                    'uncompressed_size': len(response_body),
                    'compressed_size': len(encoded_data)
                }
            except Exception as e:
                # If compression fails, fall back to uncompressed
                response_data['compression_error'] = f'Failed to compress: {str(e)}'
                response_body = json.dumps(response_data, indent=2)
        
        return {
            'statusCode': status_code,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': response_body
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'error': str(e),
                'error_type': type(e).__name__
            })
        }