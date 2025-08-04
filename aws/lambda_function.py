import json
import boto3
from pathlib import Path
import tempfile
import tarfile
import zstandard
import os


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

def lambda_handler(event, context):
    bucket_name = 'cds-peakscout-public'
    file_name = 'mouse_mm39.tar.zst'
    local_file_path = '/tmp/mouse_mm39.tar.zst'
    new_file_path = '/tmp/mouse_mm39'

    # Download file from S3 to /tmp
    s3_client = boto3.client('s3')
    try:
        s3_client.download_file(bucket_name, file_name, local_file_path)
        print(f"File '{file_name}' downloaded to '{local_file_path}'")
    except Exception as e:
        print(f"Error downloading file: {e}")
        return {"statusCode": 500, "body": "Failed to download file"}

    # Extract file
    extract_zst("/tmp/mouse_mm39.tar.zst", "/tmp/mouse_mm39")

    # Open and read the downloaded file
    '''
    try:
        with open(new_file_path, 'rb') as file:
            file_content = file.read()
            print(f"File content: {file_content[:100]}")  # Print first 100 characters
    except FileNotFoundError:
        print(f"File not found at '{new_file_path}'.")
        return {"statusCode": 500, "body": "File not found"}
    except Exception as e:
        print(f"Error reading file: {e}")
        return {"statusCode": 500, "body": "Failed to read file"}
    '''
    # List files in the extracted directory
    extracted_files = os.listdir(new_file_path)
    print(f"Files in extracted directory: {extracted_files}")

    return {
        'statusCode': 200,
        'body': "File read successfully from /tmp"
    }
