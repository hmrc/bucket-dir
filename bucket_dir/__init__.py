# -*- coding: utf-8 -*-
import logging
import sys

import botocore
import click

from .generator import BucketDirGenerator


def configure_logging(log_level="info") -> None:
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger("bucket_dir")
    logger.setLevel(log_level.upper())
    logger.addHandler(handler)
    logger.debug("Logging configured")


@click.command()
@click.argument("bucket")
@click.option(
    "--exclude-object",
    help="Exclude objects with this name from indexes. Can be specified multiple times.",
    multiple=True,
)
@click.option(
    "--target-path",
    default="/",
    help="Only generate indexes relating to a certain folder/object. E.g. '/foo-folder/bar-object'. If omitted, the entire bucket will be indexed.",
)
@click.version_option()
def run_cli(bucket, exclude_object, target_path):
    """Generate directory listings for an S3 BUCKET.

    BUCKET is the name of the bucket to be indexed."""
    configure_logging()
    logger = logging.getLogger("bucket_dir")
    bucket_dir_generator = BucketDirGenerator(logger=logger)
    try:
        bucket_dir_generator.generate(
            bucket=bucket,
            site_name=bucket,
            exclude_objects=list(exclude_object),
            target_path=target_path,
        )
    except botocore.exceptions.NoCredentialsError:
        logger.error(
            "Could not discover any AWS credentials. Please supply appropriate credentials."
        )
        sys.exit(1)
