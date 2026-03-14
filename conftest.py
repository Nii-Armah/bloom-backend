from constants import ErrorCode
import pytest


@pytest.fixture
def assert_validation_error():
    def _assert(response, field_name=None):
        assert response.status_code == 422
        data = response.json()
        assert data['success'] is False
        assert data['error']['code'] == ErrorCode.VALIDATION_ERROR
        if field_name:
            assert field_name in data['error']['details']

    return _assert


@pytest.fixture
def assert_http_error():
    def _assert(response, status_code, message=None):
        assert response.status_code == status_code
        data = response.json()
        assert data['success'] is False
        assert data['error']['code'] == ErrorCode.HTTP_ERROR
        if message:
            assert message in data['error']['message']

    return _assert


@pytest.fixture
def assert_auth_error():
    def _assert(response, status_code=401, message=None):
        assert response.status_code == status_code
        data = response.json()
        assert data['success'] is False
        assert data['error']['code'] == ErrorCode.AUTH_FAILED
        if message:
            assert message in data['error']['message']

        return True

    return _assert
