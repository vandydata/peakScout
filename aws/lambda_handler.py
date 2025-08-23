import json
import subprocess
import os
import tempfile
import shutil
from pathlib import Path

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
        max_file_size = event.get('max_file_size', 1048576)  # 1MB default
        
        if not command:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No command specified'})
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
            'temp_output_dir': temp_output_dir
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
        
        # Clean up temp directory
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