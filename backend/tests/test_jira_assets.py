from fastapi.testclient import TestClient
from app.main import app


def test_jira_import_assets_are_served():
    client = TestClient(app)
    for extension, media in [('js', 'application/javascript'), ('css', 'text/css')]:
        response = client.get(f'/static/jira-import.{extension}')
        assert response.status_code == 200
        assert media in response.headers['content-type']
        assert response.text
