import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    original = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
    }
    activities.clear()
    activities.update(original)
    yield
    activities.clear()
    activities.update(original)


class TestRoot:
    def test_root_redirects_to_static(self):
        """Verify root path redirects to static index"""
        # Arrange
        expected_status = 307
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == expected_status
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    def test_get_all_activities_returns_200(self, reset_activities):
        """Verify GET /activities returns all activities"""
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activity_has_correct_structure(self, reset_activities):
        """Verify each activity has required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        # Assert
        for field in required_fields:
            assert field in activity
        assert isinstance(activity["participants"], list)
        assert activity["max_participants"] == 12

    def test_get_activities_participants_count(self, reset_activities):
        """Verify activities load with correct participant counts"""
        # Arrange
        expected_chess_participants = 2
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert len(data["Chess Club"]["participants"]) == expected_chess_participants
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestSignup:
    def test_signup_new_participant_succeeds(self, reset_activities):
        """Verify new participant can sign up for activity"""
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_count = len(activities[activity]["participants"])
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert "message" in response.json()
        assert len(activities[activity]["participants"]) == initial_count + 1
        assert email in activities[activity]["participants"]

    def test_signup_nonexistent_activity_fails(self, reset_activities):
        """Verify signup fails when activity doesn't exist"""
        # Arrange
        activity = "Nonexistent Club"
        email = "student@mergington.edu"
        expected_status = 404
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == expected_status
        assert "not found" in response.json()["detail"].lower()

    def test_signup_duplicate_participant_fails(self, reset_activities):
        """Verify signup fails for already registered participant"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        expected_status = 400
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == expected_status
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_across_multiple_activities(self, reset_activities):
        """Verify a student can sign up for multiple activities"""
        # Arrange
        email = "alice@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={email}")
        response2 = client.post(f"/activities/{activity2}/signup?email={email}")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in activities[activity1]["participants"]
        assert email in activities[activity2]["participants"]


class TestUnregister:
    def test_unregister_existing_participant_succeeds(self, reset_activities):
        """Verify existing participant can unregister from activity"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        assert email in activities[activity]["participants"]
        initial_count = len(activities[activity]["participants"])
        
        # Act
        response = client.delete(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert len(activities[activity]["participants"]) == initial_count - 1
        assert email not in activities[activity]["participants"]

    def test_unregister_nonexistent_participant_fails(self, reset_activities):
        """Verify unregister fails for non-registered participant"""
        # Arrange
        activity = "Chess Club"
        email = "nobody@mergington.edu"
        expected_status = 404
        
        # Act
        response = client.delete(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == expected_status
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_nonexistent_activity_fails(self, reset_activities):
        """Verify unregister fails when activity doesn't exist"""
        # Arrange
        activity = "Nonexistent Club"
        email = "michael@mergington.edu"
        expected_status = 404
        
        # Act
        response = client.delete(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == expected_status
        assert "not found" in response.json()["detail"].lower()

    def test_signup_then_unregister_flow(self, reset_activities):
        """Verify full signup and unregister flow works correctly"""
        # Arrange
        activity = "Chess Club"
        email = "bob@mergington.edu"
        
        # Act - Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert unregister_response.status_code == 200
        assert email not in activities[activity]["participants"]
