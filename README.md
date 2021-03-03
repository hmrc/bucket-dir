# bucket-dir

<a href="https://github.com/hmrc"><img alt="PyPI" src="https://img.shields.io/badge/HMRC-Digital-FFA500?style=flat&labelColor=000000&logo=gov.uk"></a>
<a href="https://pypi.org/project/bucket-dir/"><img alt="PyPI" src="https://img.shields.io/pypi/v/bucket-dir"></a>
<img alt="PyPI" src="https://img.shields.io/pypi/pyversions/bucket-dir">
<a href="https://github.com/hmrc/bucket-dir/blob/master/LICENSE"><img alt="License: Apache 2.0" src="https://img.shields.io/github/license/hmrc/bucket-dir"></a>
<a href="https://github.com/hmrc/bucket-dir"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

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

Use `bucket-dir --help` for all arguments.

Be sure to provide the command with credentials that allow it to perform ListBucket and PutObject calls against the bucket. E.g. with [aws-vault](https://github.com/99designs/aws-vault):

```
aws-vault exec foo-profile -- bucket-dir foo-bucket
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

## License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").
