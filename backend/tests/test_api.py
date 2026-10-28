from app.models import ChatRequest


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "groq" in data


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Sift"
    assert "docs" in data


def test_upload_no_file_422(client):
    response = client.post("/upload")
    assert response.status_code == 422


def test_analyze_nonexistent_document(client):
    response = client.post("/analyze/nonexistent-id")
    assert response.status_code == 404


def test_list_documents_empty(client):
    response = client.get("/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_nonexistent_analysis(client):
    response = client.get("/analyses/nonexistent")
    assert response.status_code == 404


def test_chat_empty_message(client):
    response = client.post("/chat", json=ChatRequest(message="").model_dump())
    assert response.status_code == 200
    data = response.json()
    assert "Please provide a question" in data["answer"]


def test_chat_overlong_message(client):
    long_msg = "x" * 5001
    response = client.post("/chat", json=ChatRequest(message=long_msg).model_dump())
    assert response.status_code == 400


def test_delete_nonexistent_document(client):
    response = client.delete("/documents/nonexistent")
    assert response.status_code == 404
