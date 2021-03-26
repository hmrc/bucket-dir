# -*- coding: utf-8 -*-
import sys

import botocore
import click
from rich.console import Console

from .generator import BucketDirGenerator


@click.command()
@click.argument("bucket")
@click.option(
    "--target-path",
    default="/",
    help="Only generate indexes relating to a certain folder/object. E.g. '/foo-folder/bar-object'. If ommitted, the entire bucket will be indexed.",
)
@click.version_option()
def run_cli(bucket, target_path):
    """Generate directory listings for an S3 BUCKET.

    BUCKET is the name of the bucket to be indexed."""
    console = Console()
    bucket_dir_generator = BucketDirGenerator()
    try:
        bucket_dir_generator.generate(bucket=bucket, site_name=bucket, target_path=target_path)
    except botocore.exceptions.NoCredentialsError:
        console.log(
            "Could not discover any AWS credentials. Please supply appropriate credentials."
        )
        sys.exit(1)
