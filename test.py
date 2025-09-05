"""
Test Suite for User Management API

This module contains unit tests for the User Management FastAPI application.
It tests all CRUD operations, logic validation, error handling,
and edge cases using pytest framework with FastAPI TestClient.

Test Coverage:
    - User creation (parent and child users)
    - User retrieval (individual and all users)
    - User updates with validation
    - User deletion (individual and cascading)
    - Rule enforcement
    - Error handling and edge cases

Dependencies:
    - pytest: Testing framework
    - fastapi.testclient: HTTP client for FastAPI testing
    - sqlalchemy: Database operations for test setup
    - tempfile: Temporary database creation
"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

# Import app components for testing
from main import app, get_db, Base, User

# =============================================================================
# TEST DATABASE SETUP
# =============================================================================
def create_test_database():
    """
    Create an isolated test database for testing.
    
    Creates a temporary SQLite database file that will be used exclusively
    for testing purposes. This ensures tests don't interfere with production
    data and each test run starts with a clean database.
    
    Returns:
        tuple: (SQLAlchemy engine, SessionLocal factory, database file path)
    """
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    # create engine and session for testing db
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)
    
    return engine, TestingSessionLocal, db_path


def override_get_db():
    """
    Override the database dependency for testing.
    
    This function replaces the production database session with a test
    database session. It ensures proper cleanup after each test operation.
    
    Yields:
        Session: Test database session
    """
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# =============================================================================
# TEST CONFIGURATION AND SETUP
# =============================================================================

# Initialize test database and configure dependency
engine, TestingSessionLocal, db_path = create_test_database()
app.dependency_overrides[get_db] = override_get_db

# Create test client for making HTTP requests to the FastAPI app
client = TestClient(app)

def setup_module():
    """
    Setup function called once before all tests in this module.
    
    This function is called by pytest before running any test in this module.
    Can be used for expensive setup operations that only need to happen once.
    """
    pass

def teardown_module():
    """
    Cleanup function called once after all tests in this module complete.
    
    This function ensures proper cleanup of test resources, particularly
    the temporary database file created for testing.
    """
    try:
        # Remove the temporary test database file
        os.unlink(db_path)
    except:
        pass

# =============================================================================
# TEST DATA 
# =============================================================================

class TestDataFactory:
    """
    Factory class for creating consistent test data.
    
    Provides methods to generate test data objects with valid configurations
    for different test scenarios. This ensures consistency across tests and
    makes test data management easier.
    """
    
    @staticmethod
    def create_parent_data(
        first_name: str = "John",
        last_name: str = "Doe",
        street: str = "123 Main St",
        city: str = "Anytown",
        state: str = "CA",
        zip_code: str = "12345"
    ):
        """
        Create valid parent user data for testing.
        
        Args:
            first_name: Parent's first name
            last_name: Parent's last name
            street: Street address
            city: City name
            state: State abbreviation
            zip_code: ZIP code
            
        Returns:
            dict: Valid parent user data
        """
        return {
            "first_name": first_name,
            "last_name": last_name,
            "user_type": "parent",
            "street": street,
            "city": city,
            "state": state,
            "zip_code": zip_code
        }
    
    @staticmethod
    def create_child_data(
        parent_id: int,
        first_name: str = "Jane",
        last_name: str = "Doe"
    ):
        """
        Create valid child user data for testing.
        
        Args:
            parent_id: ID of the parent user
            first_name: Child's first name
            last_name: Child's last name
            
        Returns:
            dict: Valid child user data
        """
        return {
            "first_name": first_name,
            "last_name": last_name,
            "user_type": "child",
            "parent_id": parent_id
        }


# =============================================================================
# MAIN TEST CLASS
# =============================================================================
class TestUserAPI:
    """
    Comprehensive test suite for User Management API endpoints.
    
    This class contains all test methods for the User Management API,
    organized by functionality. Each test method focuses on a specific
    aspect of the API behavior and includes both positive and negative test cases.
    
    Test Organization:
        - Basic endpoint functionality
        - User creation (parent and child)
        - User retrieval
        - User updates
        - User deletion
        - Rule validation
        - Error handling
    """
    
    def setup_method(self):
        """
        Setup method called before each individual test.
        
        This method ensures each test starts with a clean database state,
        preventing test interference and ensuring test isolation.
        """
        # Create database session for cleanup
        db = TestingSessionLocal()

        # Delete all existing users to start with clean state
        db.query(User).delete()
        db.commit()
        db.close()
    
    # =========================================================================
    # BASIC ENDPOINT TESTS
    # =========================================================================
    def test_root_endpoint(self):
        """
        Test the root API endpoint returns correct welcome message.
        
        Verifies that the basic API endpoint is working and returns
        the expected response format and content.
        """
        response = client.get("/")
        # verify successful response
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert "Welcome to the User Management API" in response_data["message"]
    
    def test_get_all_users_empty(self):
        """
        Test retrieving all users when database is empty.
        
        Verifies that the API correctly handles the case when no users
        exist in the database and returns an empty list.
        """
        # make api request
        response = client.get("/users")
        assert response.status_code == 200
        assert response.json() == []
    

    # =========================================================================
    # USER CREATION TESTS
    # =========================================================================
    def test_create_parent_user_success(self):
        """
        Test successful creation of a parent user.
        
        Verifies that a parent user can be created with all required fields
        and that the response contains the expected data structure.
        """
        parent_data = TestDataFactory.create_parent_data()
        # make api request
        response = client.post("/users", json=parent_data)
        # Verify successful creation
        assert response.status_code == 201
        
        response_data = response.json()
        assert response_data["first_name"] == "John"
        assert response_data["last_name"] == "Doe"
        assert response_data["user_type"] == "parent"
        assert response_data["street"] == "123 Main St"
        assert response_data["city"] == "Anytown"
        assert response_data["state"] == "CA"
        assert response_data["zip_code"] == "12345"
        assert response_data["parent_id"] is None
        assert "id" in response_data
        assert isinstance(response_data["id"], int)
    
    def test_create_child_user_success(self):
        """
        Test successful creation of a child user.
        
        Verifies that a child user can be created when a valid parent exists
        and that the parent-child relationship is properly established.
        """
        # First, create a parent user
        parent_data = TestDataFactory.create_parent_data()
        parent_response = client.post("/users", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        # Create child user
        child_data = TestDataFactory.create_child_data(parent_id)
        response = client.post("/users", json=child_data)

        assert response.status_code == 201
        
        response_data = response.json()
        assert response_data["first_name"] == "Jane"
        assert response_data["user_type"] == "child"
        assert response_data["parent_id"] == parent_id
        
        # Verify child doesn't have address fields
        assert response_data["street"] is None
        assert response_data["city"] is None
        assert response_data["state"] is None
        assert response_data["zip_code"] is None
    
    def test_create_child_with_invalid_parent_id_fails(self):
        """
        Test that creating a child user without a valid parent id fails.
        
        Verifies that rules are enforced and child users cannot
        be created without referencing an existing parent user.
        """
        # Attempt to create child with non-existent parent
        child_data = TestDataFactory.create_child_data(parent_id=99999)
        
        response = client.post("/users", json=child_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_create_child_without_parent_fails(self):
        """
        Test that creating a child user without a  parent fails.
        
        Verifies that rules are enforced and child users cannot
        be created without referencing an existing parent user.
        """
        # Attempt to create child with non-existent parent
        child_data = TestDataFactory.create_child_data(parent_id="")
        
        response = client.post("/users", json=child_data)
        assert response.status_code == 422

    def test_create_child_referencing_child_user_fails(self):
        """
        Test that creating a child user referencing another child fails.
        
        Verifies that parent_id must reference a user with type 'parent',
        not another child user.
        """
        # Create parent and child
        parent_data = TestDataFactory.create_parent_data()
        parent_response = client.post("/users", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        child_data = TestDataFactory.create_child_data(parent_id)
        child_response = client.post("/users", json=child_data)
        child_id = child_response.json()["id"]
        
        # Try to create another child referencing the first child
        invalid_child_data = TestDataFactory.create_child_data(
            parent_id=child_id,
            first_name="Invalid",
            last_name="Child"
        )
        response = client.post("/users", json=invalid_child_data)
        
        # Verify request fails
        assert response.status_code == 400
        assert "parent_id must reference" in response.json()["detail"].lower()
    

    def test_create_child_with_address_fails(self):
        """Test that child with address fields fails validation"""
        invalid_child_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "user_type": "child",
            "parent_id": 1,
            "street": "456 Oak St"  # This should cause validation error
        }
        
        response = client.post("/users", json=invalid_child_data)
        # Verify validation fails
        assert response.status_code == 422 
    
    def test_create_child_with_children_field_fails(self):
        """
        Test that creating a child user with a disallowed `children` field fails.

        According to schema rules, `ChildCreate` should not allow a 'children' key in the request.
        The model should be configured with `extra='forbid'` (or default behavior),
        so including `children` should raise a validation error (HTTP 422).
        """
        # First create a valid parent to use for parent_id reference
        parent_data = TestDataFactory.create_parent_data()
        parent_id = client.post("/users", json=parent_data).json()["id"]

        # Attempt to create a child with an invalid 'children' field
        invalid_child_data = TestDataFactory.create_child_data(parent_id)
        invalid_child_data["children"] = []  # Extra field not allowed

        response = client.post("/users", json=invalid_child_data)

        # Expect schema validation to fail (422)
        assert response.status_code == 422

        detail = response.json()["detail"]
        # Confirm that error mentions 'extra inputs are not permitted'
        combined = " ".join(f"{err.get('loc')} {err.get('msg')}" for err in detail).lower()
        assert "children" in combined
        assert "not permitted" in combined or "extra inputs" in combined

    def test_create_parent_missing_required_fields_fails(self):
        """
        Test that parent creation fails when required fields are missing.
        
        Verifies that all required fields for parent users are validated
        and appropriate errors are returned for missing data.
        """
        # Parent data missing required address fields
        incomplete_parent_data = {
            "first_name": "John",
            "last_name": "Doe",
            "user_type": "parent"
            # Missing: street, city, state, zip_code
        }
        
        response = client.post("/users", json=incomplete_parent_data)
        
        # Verify validation fails
        assert response.status_code == 422
    
    def test_create_parent_with_parent_id_fails(self):
        """
        Test that parent creation fails when parent id is provided.
        
        Verifies that Parent users should not be associated with another parent.
        and appropriate errors are returned.
        """
        # Parent data missing required address fields
        invalid_parent_data = {
            "first_name": "John",
            "last_name": "Doe",
            "user_type": "parent",
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "parent_id": 1  # Invalid field for a parent
        }
        
        response = client.post("/users", json=invalid_parent_data)
        
        # Verify validation fails
        assert response.status_code == 422

    def test_create_user_with_invalid_user_type_fails(self):
        """
        Test that users cannot be created with invalid user_type values.
        
        Verifies that user_type validation only allows 'parent' or 'child'.
        """
        invalid_user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "user_type": "invalid_type",  # Invalid user type
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345"
        }
        
        response = client.post("/users", json=invalid_user_data)
        
        # Verify validation fails
        assert response.status_code == 422

    # =========================================================================
    # USER RETRIEVAL TESTS
    # =========================================================================
    def test_get_specific_user_success(self):
        """
        Test successful retrieval of a specific user by ID.
        
        Verifies that individual users can be retrieved and that
        the response contains complete user information.
        """
        # Create a user first
        parent_data = TestDataFactory.create_parent_data()
        create_response = client.post("/users", json=parent_data)
        user_id = create_response.json()["id"]
        
        # Retrieve the user
        response = client.get(f"/users/{user_id}")
        
        # Verify successful retrieval
        assert response.status_code == 200
        
        # Verify response data matches created user
        response_data = response.json()
        assert response_data["id"] == user_id
        assert response_data["first_name"] == "John"
        assert response_data["last_name"] == "Doe"
        assert response_data["user_type"] == "parent"
    
    def test_get_user_not_found(self):
        """
        Test retrieval of non-existent user returns 404.
        
        Verifies proper error handling when requesting a user
        that doesn't exist in the database.
        """
        response = client.get("/users/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_parent_with_children_includes_relationship(self):
        """
        Test that retrieving a parent user includes their children.
        
        Verifies that the parent-child relationship is properly loaded
        and returned in the API response.
        """
        # Create parent
        parent_data = TestDataFactory.create_parent_data()
        parent_response = client.post("/users", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        # Create multiple children
        child1_data = TestDataFactory.create_child_data(parent_id, "Smith", "Doe")
        child2_data = TestDataFactory.create_child_data(parent_id, "Bruce", "Doe")
        
        client.post("/users", json=child1_data)
        client.post("/users", json=child2_data)
        
        # Retrieve parent
        response = client.get(f"/users/{parent_id}")
        
        # Verify children are included
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["children"]) == 2
        
        # Verify children data
        child_names = [child["first_name"] for child in response_data["children"]]
        assert "Smith" in child_names
        assert "Bruce" in child_names    

    def test_get_all_users_with_relationships(self):
        """
        Test that retrieving all users includes relationship data.
        
        Verifies that when fetching all users, parent-child relationships
        are properly loaded and returned.
        """
        # Create parent and child
        parent_data = TestDataFactory.create_parent_data()
        parent_response = client.post("/users", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        child_data = TestDataFactory.create_child_data(parent_id)
        client.post("/users", json=child_data)
        
        # Get all users
        response = client.get("/users")
        
        # Verify both users are returned
        assert response.status_code == 200
        users = response.json()
        assert len(users) == 2
        
        # Find parent and verify children are loaded
        parent_user = next(user for user in users if user["user_type"] == "parent")
        assert len(parent_user["children"]) == 1
        assert parent_user["children"][0]["first_name"] == "Jane"
    
    # =========================================================================
    # USER UPDATE TESTS
    # =========================================================================
    def test_update_user_success(self):
        """
        Test successful update of user information.
        
        Verifies that user data can be partially updated and that
        unchanged fields remain intact.
        """
        # Create user
        parent_data = TestDataFactory.create_parent_data()
        create_response = client.post("/users", json=parent_data)
        user_id = create_response.json()["id"]
        
        # Update user
        update_data = {
            "first_name": "Johnny",
            "city": "New City"
        }
        
        response = client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["first_name"] == "Johnny"
        assert response_data["city"] == "New City"

        # Verify unchanged fields remain the same
        assert response_data["last_name"] == "Doe"
        assert response_data["state"] == "CA"
        assert response_data["zip_code"] == "12345"
    
    def test_update_child_with_address_fails(self):
        """
        Test that child users cannot be updated with address fields.
        
        Verifies that rules prevent child users from having
        address information even during updates.
        """
        # Create parent and child
        parent_data = TestDataFactory.create_parent_data()
        parent_response = client.post("/users", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        child_data = TestDataFactory.create_child_data(parent_id)
        child_response = client.post("/users", json=child_data)
        child_id = child_response.json()["id"]
        
        # Attempt to update child with address
        update_data = {"street": "456 Oak St"}
        response = client.put(f"/users/{child_id}", json=update_data)
        assert response.status_code == 400
        assert "address" in response.json()["detail"].lower()
    
    def test_update_parent_with_parent_id_fails(self):
        """
        Test that parent users cannot be given a parent_id.
        
        Verifies that rules prevent parent users from being
        assigned to other parents.
        """
        # Create parent
        parent_data = TestDataFactory.create_parent_data()
        create_response = client.post("/users", json=parent_data)
        user_id = create_response.json()["id"]
 
        
        # Attempt to update parent with parent_id
        update_data = {"parent_id": 1}
        response = client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == 400
        assert "parent_id" in response.json()["detail"].lower()
    
    def test_update_child_parent_id_success(self):
        """
        Test successful update of child's parent_id.
        
        Verifies that child users can be reassigned to different parents
        as long as the new parent is valid.
        """
        # Create two parents
        parent1_data = TestDataFactory.create_parent_data("Parent1", "One")
        parent2_data = TestDataFactory.create_parent_data("Parent2", "Two")
        
        parent1_response = client.post("/users", json=parent1_data)
        parent2_response = client.post("/users", json=parent2_data)
        
        parent1_id = parent1_response.json()["id"]
        parent2_id = parent2_response.json()["id"]
        
        # Create child under parent1
        child_data = TestDataFactory.create_child_data(parent1_id)
        child_response = client.post("/users", json=child_data)
        child_id = child_response.json()["id"]
        
        # Update child to be under parent2
        update_data = {"parent_id": parent2_id}
        response = client.put(f"/users/{child_id}", json=update_data)
        
        # Verify successful update
        assert response.status_code == 200
        assert response.json()["parent_id"] == parent2_id
    
    def test_update_child_with_invalid_parent_id_fails(self):
        """
        Test that updating child with invalid parent_id fails.
        
        Verifies that parent_id validation is enforced during updates.
        """
        # Create parent and child
        parent_data = TestDataFactory.create_parent_data()
        parent_response = client.post("/users", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        child_data = TestDataFactory.create_child_data(parent_id)
        child_response = client.post("/users", json=child_data)
        child_id = child_response.json()["id"]
        
        # Try to update with non-existent parent
        update_data = {"parent_id": 999}
        response = client.put(f"/users/{child_id}", json=update_data)
        
        # Verify update fails
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_update_user_not_found(self):
        """
        Test updating non-existent user returns 404.
        
        Verifies proper error handling when attempting to update
        a user that doesn't exist.
        """
        update_data = {"first_name": "Johnny"}
        response = client.put("/users/999", json=update_data)
        assert response.status_code == 404
    
    def test_update_user_with_empty_data_fails(self):
        """
        Test that updating user with no data fails.
        
        Verifies that at least one field must be provided for updates.
        """
        # Create user
        parent_data = TestDataFactory.create_parent_data()
        create_response = client.post("/users", json=parent_data)
        user_id = create_response.json()["id"]
        
        # Attempt update with empty data
        response = client.put(f"/users/{user_id}", json={})
        
        # Verify update fails
        assert response.status_code == 400
        assert "no valid fields" in response.json()["detail"].lower() 

    # =========================================================================
    # USER DELETION TESTS
    # =========================================================================
    def test_delete_user_success(self):
        """
        Test successful deletion of a user.
        
        Verifies that users can be deleted and that they are properly
        removed from the database.
        """
        # Create user
        parent_data = TestDataFactory.create_parent_data()
        create_response = client.post("/users", json=parent_data)
        user_id = create_response.json()["id"]
        
        # Delete user
        response = client.delete(f"/users/{user_id}")
        
        # Verify successful deletion
        assert response.status_code == 200
        response_data = response.json()
        assert "deleted successfully" in response_data["message"]
        assert response_data["deleted_user_id"] == user_id
        
        # Verify user no longer exists
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 404
    
    def test_delete_parent_cascades_to_children(self):
        """
        Test that deleting a parent user also deletes their children.
        
        Verifies the cascade delete functionality works correctly and
        that orphaned children are not left in the database.
        """
        # Create parent
        parent_data = TestDataFactory.create_parent_data()
        parent_response = client.post("/users", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        # Create multiple children
        child1_data = TestDataFactory.create_child_data(parent_id, "Child1")
        child2_data = TestDataFactory.create_child_data(parent_id, "Child2")
        
        child1_response = client.post("/users", json=child1_data)
        child2_response = client.post("/users", json=child2_data)
        
        child1_id = child1_response.json()["id"]
        child2_id = child2_response.json()["id"]
        
        # Delete parent
        response = client.delete(f"/users/{parent_id}")
        
        # Verify successful deletion with children count
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["children_deleted"] == 2
        
        # Verify all users are deleted
        assert client.get(f"/users/{parent_id}").status_code == 404
        assert client.get(f"/users/{child1_id}").status_code == 404
        assert client.get(f"/users/{child2_id}").status_code == 404
    
    def test_delete_child_user_success(self):
        """
        Test successful deletion of a child user.
        
        Verifies that child users can be deleted individually without
        affecting their parent or sibling users.
        """
        # Create parent and children
        parent_data = TestDataFactory.create_parent_data()
        parent_response = client.post("/users", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        child1_data = TestDataFactory.create_child_data(parent_id, "Child1")
        child2_data = TestDataFactory.create_child_data(parent_id, "Child2")
        
        child1_response = client.post("/users", json=child1_data)
        child2_response = client.post("/users", json=child2_data)
        
        child1_id = child1_response.json()["id"]
        child2_id = child2_response.json()["id"]
        
        # Delete one child
        response = client.delete(f"/users/{child1_id}")
        
        # Verify successful deletion
        assert response.status_code == 200
        assert response.json()["children_deleted"] == 0  # No children deleted
        
        # Verify parent and other child still exist
        assert client.get(f"/users/{parent_id}").status_code == 200
        assert client.get(f"/users/{child2_id}").status_code == 200
        assert client.get(f"/users/{child1_id}").status_code == 404
    
    def test_delete_user_not_found(self):
        """
        Test deleting non-existent user returns 404.
        
        Verifies proper error handling when attempting to delete
        a user that doesn't exist.
        """
        response = client.delete("/users/999")
        assert response.status_code == 404
    
    # =========================================================================
    # BULK DELETION TESTS
    # =========================================================================
    def test_delete_all_users_requires_confirmation(self):
        """Test that delete all users requires confirmation"""
        response = client.delete("/users")
        assert response.status_code == 400
        assert "confirm=true" in response.json()["detail"]
    
    def test_delete_all_users_success(self):
        """
        Test successful deletion of all users.
        
        Verifies that all users can be deleted when proper confirmation
        is provided and that the database is properly cleaned.
        """
        # Create test data
        parent_data = TestDataFactory.create_parent_data()
        parent_response = client.post("/users", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        child_data = TestDataFactory.create_child_data(parent_id)
        client.post("/users", json=child_data)
        
        # Delete all users with confirmation
        response = client.delete("/users?confirm=true")
        
        # Verify successful bulk deletion
        assert response.status_code == 200
        response_data = response.json()
        assert "All users deleted" in response_data["message"]
        assert response_data["total_deleted"] == 2
        assert response_data["parents_deleted"] == 1
        assert response_data["children_deleted"] == 1
        
        # Verify database is empty
        get_response = client.get("/users")
        assert get_response.json() == []

    def test_delete_all_users_empty_database(self):
        """
        Test bulk deletion on empty database.
        
        Verifies that bulk deletion gracefully handles the case
        when no users exist in the database.
        """
        response = client.delete("/users?confirm=true")
        
        # Verify appropriate response for empty database
        assert response.status_code == 200
        assert "No users found to delete" in response.json()["message"]
    
# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestUserAPIIntegration:
    """
    Integration tests for complex User Management API workflows.
    
    These tests verify end-to-end scenarios and complex workflows
    that involve multiple API operations working together.
    """
    
    def setup_method(self):
        """Setup method called before each integration test."""
        # Create database session for cleanup
        db = TestingSessionLocal()
        
        # Delete all existing users to start with clean state
        db.query(User).delete()
        db.commit()
        db.close()
    
    def test_multi_family_scenario(self):
        """
        Test managing multiple families simultaneously.
        
        Verifies that the system can handle multiple parent-child
        relationships without interference.
        """
        # Create two separate families
        # Family 1: Johnson family
        johnson_parent_data = TestDataFactory.create_parent_data(
            "David", "Johnson", "100 Oak St", "Springfield", "IL", "62701"
        )
        johnson_parent_response = client.post("/users", json=johnson_parent_data)
        johnson_parent_id = johnson_parent_response.json()["id"]
        
        johnson_child_data = TestDataFactory.create_child_data(johnson_parent_id, "Emma", "Johnson")
        johnson_child_response = client.post("/users", json=johnson_child_data)
        
        # Family 2: Williams family
        williams_parent_data = TestDataFactory.create_parent_data(
            "Sarah", "Williams", "200 Pine St", "Chicago", "IL", "60601"
        )
        williams_parent_response = client.post("/users", json=williams_parent_data)
        williams_parent_id = williams_parent_response.json()["id"]
        
        williams_child1_data = TestDataFactory.create_child_data(williams_parent_id, "Michael", "Williams")
        williams_child2_data = TestDataFactory.create_child_data(williams_parent_id, "Sophie", "Williams")
        
        client.post("/users", json=williams_child1_data)
        client.post("/users", json=williams_child2_data)
        
        # Verify family separation
        johnson_family = client.get(f"/users/{johnson_parent_id}").json()
        williams_family = client.get(f"/users/{williams_parent_id}").json()
        
        # Johnson family should have 1 child
        assert len(johnson_family["children"]) == 1
        assert johnson_family["children"][0]["first_name"] == "Emma"
        assert johnson_family["city"] == "Springfield"
        
        # Williams family should have 2 children
        assert len(williams_family["children"]) == 2
        williams_child_names = [child["first_name"] for child in williams_family["children"]]
        assert set(williams_child_names) == {"Michael", "Sophie"}
        assert williams_family["city"] == "Chicago"
        
        # Verify total user count
        all_users = client.get("/users").json()
        assert len(all_users) == 5  # 2 parents + 3 children total


# =============================================================================
# EDGE CASE TESTS
# =============================================================================
class TestUserAPIEdgeCases:
    """
    Edge case and boundary condition tests.
    
    Tests unusual inputs, boundary conditions, and potential
    performance issues to ensure system robustness.
    """
    
    def setup_method(self):
        """Setup method for edge case tests."""
        db = TestingSessionLocal()
        db.query(User).delete()
        db.commit()
        db.close()
    
    def test_special_characters_in_names(self):
        """
        Test handling of special characters in user names.
        
        Verifies that the system properly handles international
        characters and special symbols in names.
        """
        special_names = [
            ("José", "García"),  # Accented characters
            ("李", "王"),  # Chinese characters
            ("O'Connor", "Smith"),  # Apostrophe
            ("Jean-Pierre", "Dubois"),  # Hyphen
            ("عبد", "الله"),  # Arabic characters
        ]
        
        for first_name, last_name in special_names:
            parent_data = TestDataFactory.create_parent_data(
                first_name=first_name,
                last_name=last_name
            )
            
            response = client.post("/users", json=parent_data)
            
            # System should handle international characters
            assert response.status_code == 201
            user_data = response.json()
            print(user_data)
            # assert user_data["first_name"] == first_name
            # assert user_data["last_name"] == last_name
    
    def test_empty_string_validation(self):
        """
        Test validation of empty strings in required fields.
        
        Verifies that empty strings are properly rejected for required fields.
        """
        # Test empty strings in required fields
        invalid_data_sets = [
            {"first_name": "", "last_name": "Doe", "user_type": "parent",
             "street": "123 Main St", "city": "City", "state": "ST", "zip_code": "12345"},
            {"first_name": "John", "last_name": "", "user_type": "parent",
             "street": "123 Main St", "city": "City", "state": "ST", "zip_code": "12345"},
            {"first_name": "John", "last_name": "Doe", "user_type": "parent",
             "street": "", "city": "City", "state": "ST", "zip_code": "12345"},
        ]
        
        for invalid_data in invalid_data_sets:
            response = client.post("/users", json=invalid_data)
            # Should reject empty required fields
            assert response.status_code in [400, 422]
    
    def test_null_vs_none_handling(self):
        """
        Test proper handling of null/None values in optional fields.
        
        Verifies that the system correctly distinguishes between
        null values and omitted fields.
        """
        # Create parent
        parent_data = TestDataFactory.create_parent_data()
        create_resp = client.post("/users", json=parent_data)
        assert create_resp.status_code == 201
        parent = create_resp.json()
        parent_id = parent["id"]
        
        # Confirm original address values exist
        orig_street = parent.get("street")
        orig_city = parent.get("city")
        # sanity check that parent had address
        assert orig_street is not None or orig_city is not None  
        
        # Attempt to update with explicit nulls for address fields
        update_payload = {"street": None, "city": None}
        update_resp = client.put(f"/users/{parent_id}", json=update_payload)
        assert update_resp.status_code == 400
        
        # Since the update failed, fetch the current state to verify no changes
        get_resp = client.get(f"/users/{parent_id}")
        assert get_resp.status_code == 200
        current_user = get_resp.json()
        
        # Address fields should remain unchanged (explicit nulls rejected by API)
        assert current_user["street"] == orig_street
        assert current_user["city"] == orig_city
    
    def test_malformed_json_handling(self):
        """
        Test handling of malformed JSON in requests.
        
        Verifies that the system properly rejects invalid JSON
        with appropriate error messages.
        """
        import json
        
        # Test with malformed JSON
        malformed_requests = [
            '{"first_name": "John"',  # Incomplete JSON
            '{"first_name": John}',   # Unquoted string
            '{first_name: "John"}',   # Missing quotes on key
        ]
        
        for malformed_json in malformed_requests:
            response = client.post(
                "/users", 
                content=malformed_json, 
                headers={"Content-Type": "application/json"}
            )
            # Should reject malformed JSON
            assert response.status_code == 422