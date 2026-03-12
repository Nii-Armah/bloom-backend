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
