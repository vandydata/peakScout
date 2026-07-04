import json
import subprocess
import os
import tempfile
import shutil
import uuid
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

CRE_SPECIES = {'hg38', 'mm10'}


def download_cre(species_genome, ref_dir, bucket_name='cds-peakscout-public'):
    """
    Download and decompress a species CRE BED file from S3 into ref_dir/cre/

    Parameters
    ----------
    species_genome: str
    ref_dir:        str  path where reference is extracted (cre/ placed as sibling of gene/)
    bucket_name:    str

    Returns
    -------
    str: path to decompressed CRE BED file
    """
    cre_dir = os.path.join(ref_dir, 'cre')
    cre_path = os.path.join(cre_dir, f'{species_genome}-cre.bed')

    if os.path.exists(cre_path):
        print(f"CRE for {species_genome} already cached at {cre_path}")
        return cre_path

    os.makedirs(cre_dir, exist_ok=True)
    s3_key = f'{species_genome}-cre.bed.zst'
    zst_path = os.path.join('/tmp', s3_key)

    print(f"Downloading {s3_key} from S3...")
    boto3.client('s3').download_file(bucket_name, s3_key, zst_path)

    print(f"Decompressing {s3_key}...")
    dctx = zstandard.ZstdDecompressor()
    with open(zst_path, 'rb') as ifh, open(cre_path, 'wb') as ofh:
        dctx.copy_stream(ifh, ofh)
    os.remove(zst_path)

    print(f"CRE ready at {cre_path}")
    return cre_path


def download_and_extract_reference(species_genome_genome, bucket_name='cds-peakscout-public'):
    """
    Download and extract reference data for a given species from S3
    
    Parameters
    ----------
    species_genome_genome:     str
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
    if species_genome_genome not in species_mapping:
        raise ValueError(f"Unsupported species: {species_genome_genome}. Supported species: {list(species_mapping.keys())}")
    
    file_name = species_mapping[species_genome_genome]
    ref_dir = f'/tmp/{species_genome_genome}'
    archive_path = f'/tmp/{file_name}'
    
    # Check if reference already exists and is valid
    if os.path.exists(ref_dir):
        expected_species_dir = os.path.join(ref_dir, species_genome_genome)
        if os.path.exists(expected_species_dir):
            gene_dir = os.path.join(expected_species_dir, 'gene')
            if os.path.exists(gene_dir) and os.listdir(gene_dir):
                print(f"Reference for {species_genome_genome} already exists at {ref_dir}")
                ##return ref_dir
                return expected_species_dir  
                return expected_species_dir  
    
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
        
        # peakScout expects: ref_dir/{species_genome_genome}/gene/
        # But archives extract to: ref_dir/reference/{species_full_name}/gene/
        # We need to create a symlink or move the directory structure
        
        expected_species_dir = os.path.join(ref_dir, species_genome_genome)
        
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
            return expected_species_dir  # Return the base ref_dir, peakScout will append species/gene
            return expected_species_dir  # Return the base ref_dir, peakScout will append species/gene
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


def upload_result_to_s3(file_path: Path, run_id: str, s3_client, bucket: str, ttl: int) -> tuple:
    key = f"results/{run_id}/{file_path.name}"
    s3_client.upload_file(str(file_path), bucket, key)
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=ttl,
    )
    return url, key


# CORS helper functions - must be defined before handler()
def _cors_headers():
    # Check if we're running locally (Docker) vs AWS Lambda
    import os
    
    function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', '')
    
    # If running in AWS, use name of your deployed function (from web console)
    if function_name == 'peakscout-containerized':
        return {}  # Let Function URL handle CORS in AWS
    else:
        # Local development (function name is 'test_function' or anything else)
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
        }

    
def handler(event, context):
    
    """
    Lambda handler for peakScout - direct file uploads up to 5MB
    
    Expected input:
    {
        "command": "decompose|peak2gene|gene2peak",
        "args": ["--species_genome _genome ", "hg38", "--k", "5", ...],
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
        max_file_size = event.get('max_file_size', 5242880)  # 5MB inline threshold
        s3_bucket = event.get('s3_bucket', 'cds-peakscout-public')
        compress_response = event.get('compress_response', True)
        s3_output = event.get('s3_output', False)       # force all outputs to S3 presigned URL
        s3_output_ttl = event.get('s3_output_ttl', 3600)  # presigned URL TTL in seconds
        use_cre = event.get('use_cre', False)           # download and apply CRE annotation
        
        if not command:
            return {
                'statusCode': 400,
                'headers': _cors_headers(),  # Use _cors_headers() function
                'headers': _cors_headers(),  # Use _cors_headers() function
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
                    'headers': _cors_headers(),  # Use _cors_headers() function
                    'headers': _cors_headers(),  # Use _cors_headers() function
                    'body': json.dumps({
                        'error': f'Failed to write uploaded file {filename}: {str(e)}',
                        'error_type': 'FileUploadError'
                    })
                }
        
        # Extract species from args to download reference data
        species_genome_genome = None
        for i, arg in enumerate(args):
            if arg == '--species_genome_genome' and i + 1 < len(args):
                species_genome_genome = args[i + 1]
                break
        
        # Download and extract reference data if species is specified
        ref_dir = None
        if species_genome_genome and species_genome_genome != 'test':  # Skip download for test species
            try:
                ref_dir = download_and_extract_reference(species_genome_genome, s3_bucket)
                print(f"Reference data ready at: {ref_dir}")
                if use_cre and species_genome in CRE_SPECIES:
                    try:
                        download_cre(species_genome, ref_dir, s3_bucket)
                    except Exception as cre_err:
                        print(f"Warning: CRE download failed for {species_genome}: {cre_err}")
            except Exception as e:
                return {
                    'statusCode': 500,
                    'headers': _cors_headers(),  # Use _cors_headers() function
                    'headers': _cors_headers(),  # Use _cors_headers() function
                    'body': json.dumps({
                        'error': f'Failed to setup reference data for species {species_genome_genome}: {str(e)}',
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
                elif species_genome_genome == 'test':
                    # Keep original ref_dir for test species
                    modified_args.append(arg)
                    # Don't skip next - use the provided test reference path
                else:
                    # For real species without downloaded ref, this is an error
                    return {
                        'statusCode': 500,
                        'headers': _cors_headers(),  # Use _cors_headers() function
                        'headers': _cors_headers(),  # Use _cors_headers() function
                        'body': json.dumps({
                            'error': f'No reference data available for species {species_genome_genome}. Reference download may have failed.',
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
        
        # --ref_dir if it notprovided and ref is available
        if not ref_dir_found and ref_dir:
            modified_args.extend(['--ref_dir', ref_dir])

        # Inject --use_cre when CRE was requested and CRE file not  provided
        if use_cre and '--cre_file' not in modified_args and '--use_cre' not in modified_args:
            modified_args.append('--use_cre')

        # Build the peakScout command
        cmd = ['python3', 'src/src/peakScout'] + modified_args + [command]
        
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
            'species': species_genome_genome,
            'ref_dir_used': ref_dir
        }
        
        # debug information if requested
        if event.get('debug', False):
            response_data['debug_info'] = {
                'tmp_contents': list_tmp_contents(),
                'ref_dir_contents': list_directory_contents(ref_dir) if ref_dir else "No reference directory"
            }
        
        # If successful and return_files is enabled, return output files
        if result.returncode == 0 and return_files:
            output_files = {}
            run_id = str(uuid.uuid4())
            s3_client = boto3.client('s3')

            output_path = Path(temp_output_dir)
            if output_path.exists():
                for file_path in output_path.rglob('*'):
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            relative_path = str(file_path.relative_to(output_path))
                            use_s3 = s3_output or file_size > max_file_size

                            if use_s3:
                                try:
                                    url, s3_key = upload_result_to_s3(
                                        file_path, run_id, s3_client, s3_bucket, s3_output_ttl
                                    )
                                    output_files[relative_path] = {
                                        'type': 's3_presigned',
                                        'download_url': url,
                                        'url_expires_in': s3_output_ttl,
                                        's3_key': s3_key,
                                        'size': file_size,
                                    }
                                except Exception as e:
                                    output_files[relative_path] = {
                                        'type': 'processing_error',
                                        'error': f'S3 upload failed: {str(e)}',
                                        'size': file_size,
                                    }
                            else:
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    output_files[relative_path] = {
                                        'content_preview': get_preview(content),
                                        'content': compress_content(content),
                                        'content_compressed': True,
                                        'compression_type': 'zstd',
                                        'size': file_size,
                                        'type': 'text',
                                    }
                                except UnicodeDecodeError:
                                    with open(file_path, 'rb') as f:
                                        binary_content = f.read()
                                    output_files[relative_path] = {
                                        'content': base64.b64encode(binary_content).decode('utf-8'),
                                        'content_compressed': False,
                                        'size': file_size,
                                        'type': 'binary_base64',
                                    }
                        except Exception as e:
                            output_files[relative_path] = {
                                'type': 'processing_error',
                                'error': str(e),
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
                
                cors_headers = _cors_headers()
                cors_headers.update({
                    'Content-Encoding': 'gzip',
                    'Content-Type': 'application/json'
                })
                
                cors_headers = _cors_headers()
                cors_headers.update({
                    'Content-Encoding': 'gzip',
                    'Content-Type': 'application/json'
                })
                
                return {
                    'statusCode': status_code,
                    'headers': cors_headers,
                    'headers': cors_headers,
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
            'headers': _cors_headers(),  # Use _cors_headers() function
            'headers': _cors_headers(),  # Use _cors_headers() function
            'body': response_body
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': _cors_headers(),  # Use _cors_headers() function
            'headers': _cors_headers(),  # Use _cors_headers() function
            'body': json.dumps({
                'error': str(e),
                'error_type': type(e).__name__
            })
        }
        



def _ensure_cors(resp):
    #  CORS headers on every response
    #  CORS headers on every response
    if not isinstance(resp, dict):
        # If  original handler  returns plain strings, normalize
        # If  original handler  returns plain strings, normalize
        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps(resp),
        }
    headers = resp.get("headers", {}) or {}
    headers.update(_cors_headers())
    resp["headers"] = headers
    # Ensure body is a string as Lambda expects
    if "body" in resp and not isinstance(resp["body"], (str, bytes)):
        resp["body"] = json.dumps(resp["body"])
    return resp

def entrypoint(event, context):
    """
    Wrapper for AWS Lambda Function
    Wrapper for AWS Lambda Function
    """
    # Preflight, some browsers will send this when content-yype is JSOn
    method = (
        event.get("requestContext", {})
             .get("http", {})
             .get("method")
        or event.get("httpMethod")
        or event.get("httpMethod")
    )
    if method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": "",
        }

    # Unwrap Function URL
    # Unwrap Function URL
    payload = event
    if "body" in event:
        raw = event.get("body", "")
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw).decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if isinstance(raw, str) and raw else {}
        except Exception:
            payload = {}

    # Actually run peakScout handler
    resp = handler(payload, context)

    # Always attach CORS headers
    return _ensure_cors(resp)

