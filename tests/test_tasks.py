class TestHealth:
    def test_health_check(self, unauthenticated_client):
        response = unauthenticated_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


class TestAuth:
    def test_login_success(self, unauthenticated_client):
        response = unauthenticated_client.post(
            "/api/v1/login", json={"username": "admin", "password": "admin"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, unauthenticated_client):
        response = unauthenticated_client.post(
            "/api/v1/login", json={"username": "admin", "password": "wrong"}
        )
        assert response.status_code == 401

    def test_protected_endpoint_without_token(self, unauthenticated_client):
        response = unauthenticated_client.get("/api/v1/tasks")
        assert response.status_code == 403

    def test_protected_endpoint_with_invalid_token(self, unauthenticated_client):
        unauthenticated_client.headers["Authorization"] = "Bearer invalid-token"
        response = unauthenticated_client.get("/api/v1/tasks")
        assert response.status_code == 401

    def test_refresh_token(self, unauthenticated_client):
        # Login to get tokens
        login_response = unauthenticated_client.post(
            "/api/v1/login", json={"username": "admin", "password": "admin"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = unauthenticated_client.post(
            "/api/v1/refresh", json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["refresh_token"] == refresh_token

    def test_refresh_token_invalid(self, unauthenticated_client):
        response = unauthenticated_client.post(
            "/api/v1/refresh", json={"refresh_token": "invalid-token"}
        )
        assert response.status_code == 401

    def test_access_token_cannot_refresh(self, unauthenticated_client):
        # Login to get access token
        login_response = unauthenticated_client.post(
            "/api/v1/login", json={"username": "admin", "password": "admin"}
        )
        access_token = login_response.json()["access_token"]

        # Try to use access token as refresh token (should fail)
        response = unauthenticated_client.post(
            "/api/v1/refresh", json={"refresh_token": access_token}
        )
        assert response.status_code == 401


class TestCreateTask:
    def test_create_task_valid(self, client):
        response = client.post("/api/v1/tasks", json={"title": "Test task"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test task"
        assert data["status"] == "pending"
        assert data["description"] is None
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_task_with_all_fields(self, client):
        response = client.post("/api/v1/tasks", json={
            "title": "Full task",
            "description": "A detailed description",
            "status": "in_progress"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Full task"
        assert data["description"] == "A detailed description"
        assert data["status"] == "in_progress"

    def test_create_task_missing_title(self, client):
        response = client.post("/api/v1/tasks", json={"description": "No title"})
        assert response.status_code == 422

    def test_create_task_title_too_long(self, client):
        response = client.post("/api/v1/tasks", json={"title": "x" * 201})
        assert response.status_code == 422

    def test_create_task_invalid_status(self, client):
        response = client.post("/api/v1/tasks", json={
            "title": "Test",
            "status": "invalid_status"
        })
        assert response.status_code == 422


class TestListTasks:
    def test_list_tasks_empty(self, client):
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_tasks_populated(self, client):
        client.post("/api/v1/tasks", json={"title": "Task 1"})
        client.post("/api/v1/tasks", json={"title": "Task 2"})
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Task 1"
        assert data[1]["title"] == "Task 2"

    def test_list_tasks_filter_by_status(self, client):
        client.post("/api/v1/tasks", json={"title": "Pending", "status": "pending"})
        client.post("/api/v1/tasks", json={"title": "Done", "status": "completed"})
        response = client.get("/api/v1/tasks?status=completed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Done"

    def test_list_tasks_pagination(self, client):
        for i in range(5):
            client.post("/api/v1/tasks", json={"title": f"Task {i}"})
        response = client.get("/api/v1/tasks?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Task 2"
        assert data[1]["title"] == "Task 3"

    def test_list_tasks_invalid_pagination(self, client):
        response = client.get("/api/v1/tasks?skip=-1")
        assert response.status_code == 422
        response = client.get("/api/v1/tasks?limit=0")
        assert response.status_code == 422
        response = client.get("/api/v1/tasks?limit=101")
        assert response.status_code == 422

    def test_list_tasks_search(self, client):
        client.post("/api/v1/tasks", json={"title": "Buy groceries"})
        client.post("/api/v1/tasks", json={"title": "Call mom"})
        client.post("/api/v1/tasks", json={"title": "Buy new shoes"})
        response = client.get("/api/v1/tasks?search=buy")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("Buy" in task["title"] for task in data)


class TestGetTask:
    def test_get_task_exists(self, client):
        create_response = client.post("/api/v1/tasks", json={"title": "Test task"})
        task_id = create_response.json()["id"]
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Test task"

    def test_get_task_not_found(self, client):
        response = client.get("/api/v1/tasks/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"


class TestUpdateTask:
    def test_update_task_partial(self, client):
        create_response = client.post("/api/v1/tasks", json={"title": "Original"})
        task_id = create_response.json()["id"]
        response = client.put(f"/api/v1/tasks/{task_id}", json={"title": "Updated"})
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    def test_update_task_status(self, client):
        create_response = client.post("/api/v1/tasks", json={"title": "Test"})
        task_id = create_response.json()["id"]
        response = client.put(f"/api/v1/tasks/{task_id}", json={"status": "completed"})
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_update_task_not_found(self, client):
        response = client.put("/api/v1/tasks/999", json={"title": "Updated"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_update_task_invalid_status(self, client):
        create_response = client.post("/api/v1/tasks", json={"title": "Test"})
        task_id = create_response.json()["id"]
        response = client.put(f"/api/v1/tasks/{task_id}", json={"status": "bad"})
        assert response.status_code == 422


class TestDeleteTask:
    def test_delete_task_exists(self, client):
        create_response = client.post("/api/v1/tasks", json={"title": "To delete"})
        task_id = create_response.json()["id"]
        response = client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 204
        # Verify it's gone
        get_response = client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == 404

    def test_delete_task_not_found(self, client):
        response = client.delete("/api/v1/tasks/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
