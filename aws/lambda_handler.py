import json
import subprocess
import os

def handler(event, context):
    """
    Simple Lambda handler for peakScout
    
    Expected input:
    {
        "command": "decompose|peak2gene|gene2peak",
        "args": ["--species", "hg38", "--k", "5", ...]
    }
    """
    try:
        command = event.get('command')
        args = event.get('args', [])
        
        if not command:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No command specified'})
            }
        
        # Build the peakScout command using python3
        cmd = ['python3', 'peakScout', command] + args
        
        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd='/var/task'
        )
        
        return {
            'statusCode': 200 if result.returncode == 0 else 500,
            'body': json.dumps({
                'command': ' '.join(cmd),
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }