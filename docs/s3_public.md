# Configuring a public S3 Bucket for use with bucket-dir

This guide outlines the minimium steps required to make a browsable static website backed by S3 alone.

You may want to do this because it is quicker and easier than setting up a CloudFront distribution. But be aware that this only makes the site available over HTTP, which in most modern web browsers results in a warning. It could also be more expensive than running CloudFront depending on your use case.

## Steps

Create a new bucket in Amazon S3.

On the bucket, browse to `Properties > Static website hosting` and set the following configuration:

* Static website hosting: Enabled
* Hosting type: Host a static website
* Index document: index.html

Make a note of the `Bucket website endpoint`.

Browse to `Permissions > Block public access (bucket settings)` and untick all of the checkboxes.

> You'll be prompted to confirm that you want all of the data in your bucket to be public. This is necessary when making a static website, but keep in mind anything you put in the bucket will be available to the world.

Staying on `Permissions` edit the `Bucket policy` with the below, replacing `foo-bucket` with the name of your bucket.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::foo-bucket/*"
            ]
        }
    ]
}
```

Run `bucket-dir` against the bucket to generate the directory listings.

You should now be able to browse the bucket using the `Bucket website endpoint`.
