from http import HTTPStatus

from fastapi.testclient import TestClient

from app.app import app


def test_root_should_return_welcome_message():
    client = TestClient(app)

    response = client.get('/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Welcome to the Sensor Data API'}
