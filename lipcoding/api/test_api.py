import pytest
from django.test import Client


@pytest.mark.django_db
def test_hello_api():
    client = Client()
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}
