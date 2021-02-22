
# bucket-dir

**bucket-dir** is a utility for generating a browsable directory tree for an AWS S3 bucket.

!["Sample"](/docs/sample.png "A sample of bucket-dir output.")

It was built in order to host Maven and Ivy repositories in S3 and serve them via CloudFront, but it could meet other needs too.

> DISCLAIMER: This utility is the product of a time boxed spike. It should not be considered production ready. Use at your own risk.

## Installation

The **bucket-dir** wheel is not currently hosted anywhere. You'll need to clone the repository and build it yourself.

In order to install, first run `make build` to produce a `.whl` package. It will be created within a `dist` folder.

Once you have built the wheel, setup a virtual environment with a version of python newer than 3.8 and install with:

```
pip install /path/to/repo/dist/bucket_dir-0.1.2-py3-none-any.whl
```

## Usage

Run `bucket-dir` with the name of the bucket you wish to index as a parameter:

```
bucket-dir foo-bucket
```

Be sure to provide the command with credentials that allow it to perform ListBucket and PutObject calls against the bucket. E.g. with [aws-vault](https://github.com/99designs/aws-vault):

```
aws-vault exec foo-profile -- bucket-dir foo-bucket
```

## Development

See the `Makefile` and run the appropriate rules.

### License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").
