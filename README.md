# User Management API
A robust FastAPI-based REST API for managing parent and child users with hierarchical relationships, built with SQLAlchemy ORM and comprehensive validation.


## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Setup and Installation](#-Setup-and-Installation)
- [API Documentation](#-api-documentation)
- [Usage Examples](#-usage-examples)  
- [Database Schema](#-database-schema) 
- [Testing](#-testing)
- [Project Structure](#-project-structure)  

## ✨ Features

### Core Functionality
- **Parent User Management**: Create and manage parent users with complete address information
- **Child User Management**: Create and manage child users linked to parent accounts
- **Hierarchical Relationships**: Self-referencing parent-child relationships with cascade operations
- **Data Validation**: Comprehensive input validation using Pydantic schemas
- **Business Rule Enforcement**: Database-level constraints ensuring data integrity

### API Features
- **RESTful Design**: Standard HTTP methods and status codes
- **Comprehensive CRUD**: Create, Read, Update, Delete operations for all entities
- **Bulk Operations**: Delete all users with safety confirmation
- **Error Handling**: Detailed error responses with meaningful messages
- **Auto Documentation**: Interactive API docs with Swagger UI

### Technical Features
- **SQLAlchemy ORM**: Type-safe database operations with relationship management
- **SQLite Database**: Lightweight, embedded database for easy deployment
- **Pydantic Validation**: Request/response validation with automatic error handling
- **Dependency Injection**: Clean architecture with FastAPI's dependency system

## 🏗 Architecture

### Business Rules
- **Parent Users**: Must have complete address information, cannot have a parent
- **Child Users**: Must reference a valid parent, cannot have address fields
- **Cascade Delete**: Deleting a parent automatically removes all their children
- **Type Immutability**: User type (parent/child) cannot be changed after creation

### Technology Stack
```
┌─────────────────┐
│   FastAPI       │  ← Web Framework
├─────────────────┤
│   Pydantic      │  ← Data Validation
├─────────────────┤
│   SQLAlchemy    │  ← ORM & Database
├─────────────────┤
│   SQLite        │  ← Database Engine
└─────────────────┘
```

## 📦 Setup and Installation

### 1. Create project folder
```
mkdir user-management-api
cd user-management-api
```
### 2. Clone the Repository in the current directory
```bash
git clone https://github.com/yourusername/user-management-api.git
cd user-management-api
```
### 3. Create Virtual env
```
python -m venv .venv
```
### 4. Activate virtual env
- macos/ Linux
```
source .venv/bin/activate
```
- Windows
```
.venv\Scripts\Activate.ps1
```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

### 6. Run the Application
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000

```
### 7. Run test
```bash
pytest test.py
```


## 📖 API Documentation
- **Base url**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/users` | Get all users |
| GET | `/users/{user_id}` | Get specific user |
| POST | `/users` | Create new user |
| PUT | `/users/{user_id}` | Update user |
| DELETE | `/users/{user_id}` | Delete user |
| DELETE | `/users?confirm=true` | Delete all users |

### Request/Response Schemas

#### Parent User Creation
```json
{
  "first_name": "string",
  "last_name": "string",
  "user_type": "parent",
  "street": "string",
  "city": "string", 
  "state": "string",
  "zip_code": "string"
}
```

#### Child User Creation
```json
{
  "first_name": "string",
  "last_name": "string",
  "user_type": "child",
  "parent_id": 1
}
```

#### User Response
```json
{
  "id": 0,
  "first_name": "string",
  "last_name": "string", 
  "user_type": "parent",
  "street": "string",
  "city": "string",
  "state": "string",
  "zip_code": "string",
  "parent_id": null,
  "children": []
}
```

### Status Codes
- `200 OK` - Successful GET, PUT, DELETE
- `201 Created` - Successful POST
- `400 Bad Request` - Invalid input or business rule violation
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## 🧾 Usage Examples
FastAPI automatically generates interactive docs where you can try every endpoint without any external tool:
### Make sure the server is running.
### Option 1 : Open the Swagger UI in your browser:
1. Open your browser at: ```http://127.0.0.1:8000/docs```
2. Click on the endpoint you want to test (e.g., `POST /users`).
3. Click **Try it out**.
4. If required, fill in the request body (for creating or updating users).
5. Click **Execute** — the response will appear below with status code and payload.

### Option 2 : Postman
1. Open Postman and create a new request.  
2. For example, to fetch all users, set:
   - Method: **GET**
   - URL:  
     ```
     http://127.0.0.1:8000/users
     ```
3. To create a new user, switch to **POST**, and add a JSON body like:

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "parent",
  "street": "123 Main St",
  "city": "Anytown",
  "state": "CA",
  "zip_code": "12345"
}
```
4. Click **Send** — you should see the response with the created user.

## 🗄 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    user_type VARCHAR NOT NULL,
    street VARCHAR,
    city VARCHAR,
    state VARCHAR,
    zip_code VARCHAR,
    parent_id INTEGER REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT valid_user_type CHECK (user_type IN ('parent', 'child')),
    CONSTRAINT parent_no_parent_id CHECK (NOT (user_type = 'parent' AND parent_id IS NOT NULL)),
    CONSTRAINT child_must_have_parent CHECK (NOT (user_type = 'child' AND parent_id IS NULL)),
    CONSTRAINT child_no_address CHECK (NOT (user_type = 'child' AND 
        (street IS NOT NULL OR city IS NOT NULL OR state IS NOT NULL OR zip_code IS NOT NULL)))
);
```
## 🧪 Testing

### Example Test Run
```bash
pytest test.py
```

### Test Coverage
The test suite includes:
- **Unit Tests**: Individual endpoint testing
- **Integration Tests**: Complex workflow testing
- **Edge Case Tests**: Boundary conditions and error handling
- **Logic Tests**: Rule enforcement validation


## 📁 Project Structure

```
user-management-api/
├── main.py                 # FastAPI application and endpoints
├── test.py                 # Comprehensive test suite
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
└── user.db           # SQLite database (auto-created)

```

