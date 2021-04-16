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
    logger.debug("Logging configured.")


@click.command()
@click.argument("bucket")
@click.option(
    "--exclude-object",
    help="Exclude objects with this name from indexes. Can be specified multiple times.",
    multiple=True,
)
@click.option(
    "--log-level",
    default="info",
    help="Logging verbosity. Default is info.",
    type=click.Choice(["debug", "info", "warning"], case_sensitive=False),
)
@click.option(
    "--single-threaded",
    default=False,
    help="Do not using multithreading. Will be slower but less intensive.",
    is_flag=True,
)
@click.option(
    "--target-path",
    default="",
    help="Only generate indexes relating to a certain folder/object. E.g. '/foo-folder/bar-object'. If omitted, the entire bucket will be indexed.",
)
@click.option(
    "--site-name",
    help="Will appear as the title on the index pages. Defaults to the BUCKET",
    default=None,
)
@click.version_option()
def run_cli(bucket, exclude_object, log_level, single_threaded, target_path, site_name):
    """Generate directory listings for an S3 BUCKET.

    BUCKET is the name of the bucket to be indexed."""
    configure_logging(log_level=log_level)
    logger = logging.getLogger("bucket_dir")

    if not site_name:
        site_name = bucket

    bucket_dir_generator = BucketDirGenerator(
        logger=logger, bucket_name=bucket, site_name=site_name
    )
    try:
        bucket_dir_generator.generate(
            extra_exclude_objects=list(exclude_object),
            single_threaded=single_threaded,
            target_path=target_path,
        )
    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "AccessDenied":
            logger.error(
                f"Access denied when making a {error.operation_name} call. Please ensure appropriate AWS permissions are set."
            )
        else:
            logger.error(f"An unhandled ClientError occured when interacting with AWS: '{error}'.")
        sys.exit(1)
    except botocore.exceptions.NoCredentialsError:
        logger.error(
            "Could not discover any AWS credentials. Please supply appropriate AWS credentials."
        )
        sys.exit(1)
