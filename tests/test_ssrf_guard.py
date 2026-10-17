"""Unit Tests for SSRF Protection Guard"""

import pytest
from app.services.ssrf_guard import validate_target_url, SSRFSecurityException
from app.config import settings


def test_ssrf_rejects_non_http():
    with pytest.raises(SSRFSecurityException, match="não suportado"):
        validate_target_url("ftp://example.com/file.txt")

    with pytest.raises(SSRFSecurityException, match="não suportado"):
        validate_target_url("file:///etc/passwd")


def test_ssrf_blocks_localhost_and_internal():
    # Temporariamente forçar verificação de IPs estritos
    orig = settings.ALLOW_PRIVATE_IPS
    settings.ALLOW_PRIVATE_IPS = False
    try:
        with pytest.raises(SSRFSecurityException):
            validate_target_url("http://localhost:8080/admin")

        with pytest.raises(SSRFSecurityException):
            validate_target_url("http://127.0.0.1:8000/metrics")

        with pytest.raises(SSRFSecurityException):
            validate_target_url("http://169.254.169.254/latest/meta-data/")

        with pytest.raises(SSRFSecurityException):
            validate_target_url("http://192.168.1.1/router")

        with pytest.raises(SSRFSecurityException):
            validate_target_url("http://10.0.0.5:5432")
    finally:
        settings.ALLOW_PRIVATE_IPS = orig


def test_valid_public_url():
    settings.ALLOW_PRIVATE_IPS = True
    url = "https://www.mercadolivre.com.br/produto/p/MLB12345"
    assert validate_target_url(url) == url
