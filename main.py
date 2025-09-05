"""
User Management API

A FastAPI application for managing parent and child users with proper relationships,
validation, and CRUD operations. Parent users have address information and can have
multiple children. Child users are linked to a single parent and cannot have address fields.

Dependencies:
    - FastAPI: Web framework for building APIs
    - SQLAlchemy: ORM for database operations
    - Pydantic: Data validation and serialization
"""


from fastapi import FastAPI, HTTPException, Depends, status 
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from pydantic import BaseModel, field_validator, Field
from typing import Optional,List, Union 

# initializing app
app = FastAPI(title="User Management API")

# =============================================================================
# DATABASE SETUP
# =============================================================================

# Create SQLite database engine with connection settings
# check_same_thread=False allows multiple threads to use the same connection
engine = create_engine("sqlite:///user.db", connect_args={"check_same_thread": False})

# creates session for db operations
LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for SQLAlchemy models
Base = declarative_base()


# =============================================================================
# DATABASE MODEL
# =============================================================================
class User(Base):
    """
    SQLAlchemy User model representing both parent and child users.
    
    Rules:
    - Parent users: Have address fields, no parent_id, can have children
    - Child users: No address fields, must have parent_id, cannot have children
    - Self-referencing relationship between parents and children
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Required fields for all users
    first_name = Column(String, nullable=False, index=True)
    last_name = Column(String, nullable=False, index=True)
    user_type = Column(String, nullable=False, index=True)
    
    # Address fields (only for Parent users)
    street = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    
    # Foreign key to establish parent child relationship
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # SQLAlchemy relationships for ORM navigation
    # One-to-many: Parent can have multiple children
    # cascade="all, delete-orphan" means delete children when parent is deleted
    children = relationship("User", back_populates="parent",cascade="all, delete-orphan")
    
    # Many-to-one: Child belongs to one parent
    # remote_side=[id] Specifies which side is the "one" in one-to-many
    parent = relationship("User", back_populates="children", remote_side=[id])
    
    # Database constraints to enforce rules
    __table_args__ = (
        # Constraint 1: user_type must be either 'parent' or 'child'
        CheckConstraint(
            "user_type IN ('parent', 'child')",
            name="valid_user_type"
        ),
        # Constraint 2: Parent users cannot have a parent_id
        CheckConstraint(
            "NOT (user_type = 'parent' AND parent_id IS NOT NULL)",
            name="parent_no_parent_id"
        ),
         # Constraint 3: Child users must have a parent_id
        CheckConstraint(
            "NOT (user_type = 'child' AND parent_id IS NULL)",
            name="child_must_have_parent"
        ),
        # Constraint 4: Child users cannot have address fields
        CheckConstraint(
            """NOT (user_type = 'child' AND 
                   (street IS NOT NULL OR city IS NOT NULL OR 
                    state IS NOT NULL OR zip_code IS NOT NULL))""",
            name="child_no_address"
        ),
    )
    
    def __repr__(self):
        """String representation for debugging"""
        return f"<User(id={self.id}, name='{self.first_name} {self.last_name}', type='{self.user_type}')>"

# Create all database tables based on defined model
Base.metadata.create_all(bind=engine)

# =============================================================================
# PYDANTIC(VALIDATOR) SCHEMAS/MODELS
# =============================================================================
class UserBase(BaseModel):
    """
    Base Pydantic model containing common fields for all users.
    Used as a parent class for other user schemas.
    """
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    user_type: str
    
    @field_validator('user_type')
    def validate_user_type(cls, v):
        if v not in ['parent', 'child']:
            raise ValueError('user_type must be either parent or child')
        return v
    
class ParentCreate(UserBase):
    """
    Schema for creating parent users.
    Includes required address fields and enforces user_type='parent'.
    """
    user_type: str = 'parent' # Default and required value
    street: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    zip_code: str = Field(..., min_length=1)
    
    # Ensure `user_type` is strictly 'parent' in this schema
    @field_validator('user_type')
    def must_be_parent(cls, v):
        if v != 'parent':
            raise ValueError('Provide valid inputs for child users')
        return v
    # disallow empty strings for required fields
    @field_validator('first_name', 'last_name', 'street', 'city','state','zip_code')
    def validate_not_empty_string(cls, v):
        if isinstance(v, str) and v.strip() == '':
            raise ValueError('Field cannot be empty string')
        return v.strip() if isinstance(v, str) else v
    
    # raise error when unknown fields are send while parent creation
    model_config = {
        'extra': 'forbid', # Ensure string validation
        'validate_strings': True,
    }

class ChildCreate(UserBase):
    """
    Schema for creating child users.
    Includes required parent_id and enforces user_type='child'.
    """
    user_type: str = 'child'
    parent_id: int
    
    @field_validator('user_type')
    def must_be_child(cls, v):
        if v != 'child':
            raise ValueError('Provide valid inputs for child users')
        return v
    
    # raise error when unknown fields are send while parent creation
    model_config = {
        'extra': 'forbid' 
    }


class UserResponse(BaseModel):
    """
    Schema for API responses containing user data.
    Includes all possible fields and nested children for parent users.
    """
    id: int
    first_name: str
    last_name: str
    user_type: str
    # Optional address fields (only present for parent users)
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    # Relationship fields
    parent_id: Optional[int] = None
    children: Optional[List['UserResponse']] = []
    # Enable ORM mode to work with SQLAlchemy models
    model_config = {'from_attributes': True}

class UserUpdate(BaseModel):
    """
    Schema for updating existing users.
    All fields are optional to allow partial updates.
    Business rule validation is handled in the endpoint logic.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    parent_id: Optional[int] = None
    # raise error when unknown fields are send while parent creation
    model_config = {'extra': 'forbid'}

# Rebuild model to resolve forward references in self-referencing relationship
UserResponse.model_rebuild()


# =============================================================================
# DEPENDENCY FUNCTIONS
# =============================================================================
def get_db():
    """
    Database session dependency for FastAPI endpoints.
    
    Creates a new database session for each request and ensures
    it's properly closed after the request is completed.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = LocalSession()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# API ENDPOINTS
# =============================================================================        
@app.get("/")
def root():
    """
    Root endpoint with API welcome message.
    
    Returns:
        dict: Welcome message and basic API information
    """
    return {
        "message": "Welcome to the User Management API",
        "version": "1.0.0",
        "author":"Amanat",
        "documentation": "/docs for API documentation"
    }

@app.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    """
    Retrieve all users from the database.
    Returns a list of all users with their children populated for parent users.

    Args:
        db: Database session dependency(needed for all endpoints)
        
    Returns:
        List[User]: All users in the database with relationships loaded
        
    Raises:
        HTTPException: 500 if database operation fails
    """
    try:
        users = db.query(User).all()
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}"
        )


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific user by their unique ID.
    
    For parent users, this will include their children in the response.
    
    Args:
        user_id: The unique identifier of the user to retrieve
        
    Returns:
        User: The requested user with relationships loaded
        
    Raises:
        HTTPException: 404 if user not found, 500 for database errors
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        return user
    # Re-raise intentional HTTPExceptions (e.g., 404) to preserve their status and details; 
    # otherwise, FastAPI would wrap them as 500
    except HTTPException:
        raise
    # Catch any unexpected non-HTTP exceptions like database errors 
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )
    
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: Union[ParentCreate, ChildCreate], db: Session = Depends(get_db)):
    """
    Create a new user (either Parent or Child).
    
    Rules Enforced:
    - Parent users: Must provide address fields, cannot have parent_id
    - Child users: Must provide valid parent_id, cannot have address fields
    - Parent existence and type validation for child users
    
    Args:
    - user_data: in the following format
    - **parent:** 
    {
        "first_name": "string",
        "last_name": "string",
        "user_type": "parent",
        "street": "string",
        "city": "string",
        "state": "string",
        "zip_code": "string"
    }
    - **child:** 
    {
        "first_name": "string",
        "last_name": "string",
        "user_type": "child",
        "parent_id": int
    }
        
    Returns:
        User: The newly created user
        
    Raises:
        HTTPException: 400 for validation errors, 500 for database errors
    """
    try:
        # Convert Pydantic model to dict
        user_dict = user_data.model_dump()
        
        # Additional validation for child users
        if user_dict['user_type'] == 'child':
            # Verify the specified parent exists
            parent = db.query(User).filter(User.id == user_dict['parent_id']).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent user with id {user_dict['parent_id']} not found"
                )
            # Verify the referenced user is actually a parent
            if parent.user_type != 'parent':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="parent_id must reference a user with user type 'parent'"
                )
        
        # Create new user instance
        new_user = User(**user_dict)
        
        # Persist to database
        db.add(new_user)
        db.commit()
        # Reload to get assigned ID and relationships
        db.refresh(new_user)
        
        return new_user
        
    except HTTPException:
        raise
    except ValueError as e:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        # Rollback transaction on unexpected errors
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """
    Update an existing user with partial data.
    
    Rules Enforced:
    - Cannot change user_type (parent/child status is immutable)
    - Parent users cannot be assigned a parent_id
    - Child users cannot be given address fields
    - Parent_id changes must reference valid parent users
    
    Args:
        user_id: ID of the user to update
        user_data: Partial user data for updates
        
    Returns:
        User: The updated user
        
    Raises:
        HTTPException: 404 if user not found, 400 for validation errors, 500 for database errors
    """
    try:
        # Get existing user
        existing_user = db.query(User).filter(User.id == user_id).first()
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        # Filter out None values to create update dictionary
        update_dict = {field: value for field, value in user_data.model_dump().items() if value is not None}
        
        # Validate that at least one field is being updated
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update"
            )
        
        # Validate rules based on existing user type
        user_type = existing_user.user_type

        # Validation for parent users
        # Parents cannot be assigned to other parents
        if user_type == 'parent':
            if 'parent_id' in update_dict and update_dict['parent_id'] is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent users cannot have a parent_id"
                )
        
        # Validation for child users
        elif user_type == 'child':
            # Children cannot have address information
            address_fields = ['street', 'city', 'state', 'zip_code']
            for field in address_fields:
                if field in update_dict and update_dict[field] is not None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Child users cannot have address field: '{field}'"
                    )
            
            # Validate new parent if parent_id is being updated
            if 'parent_id' in update_dict:
                new_parent = db.query(User).filter(User.id == update_dict['parent_id']).first()

                # Validate parent existence
                if not new_parent:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Parent user with id {update_dict['parent_id']} not found"
                    )
                
                # Validate parent user type
                if new_parent.user_type != 'parent':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="parent_id must reference a user with user type 'parent'"
                    )
        
        # Update the user
        for field, value in update_dict.items():
            setattr(existing_user, field, value)
        
        # Persist changes
        db.commit()
        db.refresh(existing_user)
        
        return existing_user
    
    # Re-raise HTTP exceptions without modification
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific user by ID.
    
    Important: If deleting a parent user, all their children will be automatically
    deleted due to the cascade="all, delete-orphan" relationship configuration.
    
    Args:
        user_id: ID of the user to delete
        
    Returns:
        dict: Success message with deletion details
        
    Raises:
        HTTPException: 404 if user not found, 500 for database errors
    """
    try:
        # Get the user to delete
        user_to_delete = db.query(User).filter(User.id == user_id).first()
        
        if not user_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        # Store info for response message
        user_type = user_to_delete.user_type
        user_name = f"{user_to_delete.first_name} {user_to_delete.last_name}"
        
        # Count children for informative response (if parent)
        children_count = 0
        if user_type == 'parent':
            children_count = db.query(User).filter(User.parent_id == user_id).count()
        
        # Delete user (cascade will handle children automatically)
        db.delete(user_to_delete)
        db.commit()
        
        # Create response message
        message = f"User '{user_name}' (ID: {user_id}) deleted successfully"
        if user_type == 'parent' and children_count > 0:
            message += f" along with {children_count} child user(s)"
        
        return {
            "message": message,
            "deleted_user_id": user_id,
            "deleted_user_type": user_type,
            "children_deleted": children_count if user_type == 'parent' else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )
    
@app.delete("/users")
def delete_all_users(confirm: bool = False, db: Session = Depends(get_db)):
    """
    Delete all users from the database.
    
    WARNING: This is a destructive operation that cannot be undone!
    Requires explicit confirmation via query parameter to prevent accidental deletion.
    
    Args:
        confirm: Must be True to execute deletion (query parameter: ?confirm=true)
        
    Returns:
        dict: Success message with deletion statistics
        
    Raises:
        HTTPException: 400 if not confirmed, 500 for database errors
        
    Example:
        DELETE /users?confirm=true
    """
    # Require explicit confirmation to proceed
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="To delete all users, you must pass confirm=true as a query parameter"
        )
    
    try:
        # Count total users before deletion
        total_users = db.query(User).count()
        parent_count = db.query(User).filter(User.user_type == 'parent').count()
        child_count = db.query(User).filter(User.user_type == 'child').count()
        
        # if database is empty simply return message
        if total_users == 0:
            return {"message": "No users found to delete"}
        
        # Delete all users
        db.query(User).delete()
        db.commit()
        
        return {
            "message": f"All users deleted successfully",
            "total_deleted": total_users,
            "parents_deleted": parent_count,
            "children_deleted": child_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting all users: {str(e)}"
        )
