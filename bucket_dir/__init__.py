# -*- coding: utf-8 -*-
import sys

import botocore
import click
from rich.console import Console

from .bucket_dir_generator import BucketDirGenerator


@click.command()
@click.argument("bucket")
@click.version_option()
def run_cli(bucket):
    """Generate directory listings for an S3 BUCKET.

    BUCKET is the name of the bucket to be indexed."""
    console = Console()
    bucket_dir_generator = BucketDirGenerator(console=console)
    try:
        bucket_dir_generator.generate(bucket=bucket, site_name=bucket)
    except botocore.exceptions.NoCredentialsError:
        console.log(
            "Could not discover any AWS credentials. Please supply appropriate credentials."
        )
        sys.exit(1)
