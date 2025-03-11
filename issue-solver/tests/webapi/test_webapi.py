from fastapi.testclient import TestClient

from issue_solver.webapi.main import app

client = TestClient(app)


def test_read_main():
    response = client.post("/repositories", json={"url": "", "accessToken": ""})
    assert response.status_code == 201
