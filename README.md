# bucket-dir

<a href="https://github.com/hmrc"><img alt="HMRC: Digital" src="https://img.shields.io/badge/HMRC-Digital-FFA500?style=flat&labelColor=000000&logo=gov.uk"></a>
<a href="https://pypi.org/project/bucket-dir/"><img alt="PyPI" src="https://img.shields.io/pypi/v/bucket-dir"></a>
<a href="https://pypi.org/project/bucket-dir/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/bucket-dir"></a>
<a href="https://github.com/hmrc/bucket-dir/blob/master/LICENSE"><img alt="License: Apache 2.0" src="https://img.shields.io/github/license/hmrc/bucket-dir"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

**bucket-dir** is a utility for generating a browsable directory tree for an AWS S3 bucket.

!["Sample image"](/docs/sample.png "A sample of bucket-dir output.")

It was built in order to host Maven and Ivy repositories in S3 and serve them via CloudFront, but it could meet other needs too.

## Installation

```
pip install bucket-dir
```
## Usage

Run `bucket-dir` with the name of the bucket you wish to index as a parameter:

```
bucket-dir foo-bucket
```

If you only want to upload indexes for a particular part of the bucket, use `--target-path`. This will generate indexes for folders that lead to the path, and everything under the path:

```
# These all update the root index, foo-folder's index, and everything underneath foo-folder
bucket-dir foo-bucket --target-path '/foo-folder/foo-object'
bucket-dir foo-bucket --target-path '/foo-folder/'
bucket-dir foo-bucket --target-path 'foo-folder/foo-object'
bucket-dir foo-bucket --target-path 'foo-folder/'
```

If you need to exclude objects with certain names from the index use `--exclude-object`. This will hide any objects that match this name. `index.html` objects are ignored for free:

```
bucket-dir foo-bucket --exclude-object 'error.html' --exclude-object 'foo-object'
```

Use `bucket-dir --help` for all arguments.

Be sure to provide the command with credentials that allow it to perform ListBucket and PutObject calls against the bucket. E.g. with [aws-vault](https://github.com/99designs/aws-vault):

```
aws-vault exec foo-profile -- bucket-dir foo-bucket
```
### IAM requirements

This example demonstrates the most restrictive policy you can apply to the principal (e.g. an IAM user or role) that is going to run `bucket-dir`. Substitute `foo-bucket` for the name of your bucket:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::foo-bucket"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::foo-bucket/index.html",
                "arn:aws:s3:::foo-bucket/*/index.html"
            ]
        }
    ]
}
```

* `s3:ListBucket` is required for `bucket-dir` to be able to map out the folders and objects that the bucket contains.
* `s3:PutObject` is required for `bucket-dir` to be able to upload generated `index.html` documents.
* `s3:DeleteObject` is required for `bucket-dir` to be able to remove redundant `index.html` documents.


### Example AWS configuration

For examples on how you can configure an S3 bucket to serve static site content indexed by `bucket-dir`, see:

* [Configuring a public S3 Bucket for use with bucket-dir.](docs/s3_public.md)

Examples of how you can front public and private buckets with CloudFront, and how bucket-dir can be run in a lambda, will be added in due course.

### Using bucket-dir as a library

`bucket-dir` can also be used as a dependency of your own python applications.

```
from bucket_dir import BucketDirGenerator

BucketDirGenerator(bucket_name="foo-bucket", site_name="my static site").generate()
```

### Character support

`bucket-dir` supports objects using any of the _Safe characters_ listed in the S3 [object key naming guidelines](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html#object-key-guidelines).

The exception to the above rule is using forward slashes consecutively (e.g. `my-folder//my-object`). This results in a folder called `/`, which breaks hyperlinks.

Use of characters in the _Characters that might require special handling_ list is currently unsupported but is theoretically ok.

Some characters in _Characters to avoid_ may also work, but you're on your own.

## Development

Start with `make init`. This will install prerequisties and set up a poetry managed virtual environment containing all the required runtime and development dependencies.

Unit testing can be performed with `make test`. If you want to run pytest with other options, use `poetry run pytest ...`.

You can execute the source code directly with `poetry run bucket-dir`.

Finally, you can build with `make build`. This will update dependencies, run security checks and analysis and finally package the code into a wheel and archive.

Publishing can be performed with `make publish`, but this is only intended to run in CI on commit to the main branch. If running locally, you need to have PyPI credentials set as env vars.

For other rules, see the [Makefile](Makefile).

If you are a collaborator, feel free to make changes directly to the main branch. Otherwise, please raise a PR. Don't forget to bump the version in [pyproject.toml](pyproject.toml).

### Profiling

To get a performance profile, use:

```
make profile
```

You must have the `graphviz` library installed.

A `combined.svg` image will be generated in the `prof` directory which you can use to find bottlenecks and potential enhancements.

## License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").
