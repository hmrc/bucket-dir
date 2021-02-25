# bucket-dir

<a href="https://pypi.org/project/bucket-dir/"><img alt="PyPI" src="https://img.shields.io/pypi/v/bucket-dir"></a>
<img alt="PyPI" src="https://img.shields.io/pypi/pyversions/bucket-dir">
<a href="https://github.com/hmrc/bucket-dir/blob/master/LICENSE"><img alt="License: Apache 2.0" src="https://img.shields.io/github/license/hmrc/bucket-dir"></a>
<a href="https://github.com/hmrc/bucket-dir"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

**bucket-dir** is a utility for generating a browsable directory tree for an AWS S3 bucket.

!["Sample image"](/docs/sample.png "A sample of bucket-dir output.")

It was built in order to host Maven and Ivy repositories in S3 and serve them via CloudFront, but it could meet other needs too.

> DISCLAIMER: This utility is the product of a time boxed spike. It should not be considered production ready. Use at your own risk.

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

## Development

Start with `make init`. This will install prerequisties and set up a poetry managed virtual environment containing all the required runtime and development dependencies.

Unit testing can be performed with `make test`. If you want to run pytest with other options, use `poetry run pytest ...`.

Finally, you can build with `make build`. This will update dependencies, run security checks and analysis and finally package the code into a wheel and archive.

Publishing can be performed with `make publish`, but this is only intended to run in CI on commit to the main branch. If running locally, you need to have PyPI credentials set as env vars.

For other rules, see the [Makefile](Makefile).

If you are a collaborator, feel free to make changes directly to the main branch. Otherwise, please raise a PR. Don't forget to bump the version in [pyproject.toml](pyproject.toml).

### Using the local bucket-dir script

You can use the provided `bucket-dir` script from the root of the repo to run the code without having to build and install it. Keep in mind that you'll need to provide a path and run it within the virtual environment (e.g. `poetry run ./bucket-dir --help`).

## License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").
