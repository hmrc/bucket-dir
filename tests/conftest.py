# -*- coding: utf-8 -*-
import pytest


@pytest.fixture
def aws_creds(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "foo-aws-access-key-id")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "foo-aws-secret-access-key")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-1")


@pytest.fixture
def delete_aws_creds(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
