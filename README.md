<div align="center">
  <h1>🚀 FastAPI Project Management System</h1>
  <p><strong>A Production-Grade RESTful API for Team Collaboration & Task Management</strong></p>
</div>

## 📑 Overview

This repository contains the backend infrastructure for a robust Project Management System. Built with **FastAPI** and **MySQL**, this project moves beyond standard CRUD operations to tackle real-world system design challenges. It implements strict **Clean Architecture**, a **Defense-in-Depth** security model, and guarantees **Data Consistency** through atomic database transactions.

---

## ✨ Core Engineering & Architecture

### 1. Clean Architecture (3-Tier Separation)
The codebase is strictly layered to ensure maintainability, scalability, and testability:
*   **Router Layer:** Dedicated exclusively to handling HTTP requests, Pydantic payload validation, and dependency injection.
*   **Service Layer:** The core orchestrator. Encapsulates business logic, manages Dual-Logging, and dictates atomic database transaction boundaries (`db.commit()` and `db.rollback()`).
*   **Repository Layer:** Isolated database interaction layer. Responsible for query execution and session staging (`db.flush()`), remaining entirely agnostic of HTTP context.

### 2. Defense-in-Depth Security Model
*   **Dual-Layer Authorization:**
    *   *Layer 1 (Stateless Gatekeeper):* JWT-based scope verification efficiently drops unauthorized requests before they consume database resources.
    *   *Layer 2 (Stateful RBAC):* Dynamic, context-aware Resource-Based Access Control validates user roles (`OWNER`, `MEMBER`, `ASSIGNEE`) against real-time database state, structurally neutralizing IDOR/BOLA vulnerabilities.
*   **RFC 6749 Compliant Token Management:**
    *   Implements **Stateful Refresh Tokens** with **Token Rotation**.
    *   Features **Automatic Reuse Detection**: If a compromised, previously-revoked token is submitted, the system triggers a security breach protocol, instantly invalidating all active sessions for the targeted user.

### 3. Data Integrity & Concurrency Control
*   **Atomic Transactions:** Multi-step operations (e.g., creating a task and recording the audit log) are executed within a single transaction unit to prevent partial data writes.
*   **Pessimistic Locking:** Utilizes `FOR UPDATE` queries to prevent race conditions during critical state mutations (e.g., verifying the last remaining project owner before deletion).

### 4. Dual-Logging & Audit Trails
*   **System Logs:** Standard console I/O for real-time monitoring and debugging.
*   **Business Audit Trail (`ActivityLog`):** Critical user operations are permanently persisted to the database within the same transaction boundary as the primary action, providing an immutable history of system events.

---

## 💻 Technology Stack

*   **Core Framework:** Python 3.10+, FastAPI, Uvicorn
*   **Database:** MySQL
*   **ORM & Migrations:** SQLAlchemy 2.0, Alembic
*   **Security & Crypto:** PyJWT, Passlib (Bcrypt)
*   **Data Validation:** Pydantic V2

---

## ⚙️ Getting Started
### Prerequisites
*   Python 3.10 or higher
*   MySQL Server running locally or via Docker

### Installation

**1. Clone the repository and set up a virtual environment**
```bash
git clone [https://github.com/minhhieu110907/NguyenMinhHieu_B25DTCN240_FastAPI_Project.git](https://github.com/minhhieu110907/NguyenMinhHieu_B25DTCN240_FastAPI_Project.git)
cd NguyenMinhHieu_B25DTCN240_FastAPI_Project

python -m venv venv
# On Linux/macOS:
source venv/bin/activate  
# On Windows:
venv\Scripts\activate
2. Install dependencies

Bash
pip install -r requirements.txt
3. Configure Environment Variables
Create a .env file in the root directory. Use your .env.example as a reference:

Đoạn mã
# MySQL Database Configuration
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/project_management_db

# Security Configuration
SECRET_KEY=your_super_secret_key
ALGORITHM=HS256

# Token Lifespans
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAY=7
4. Run Database Migrations and Start the Server

Bash
alembic upgrade head
uvicorn app.main:app --reload
📖 API Documentation
Once the server is running, navigate to the auto-generated interactive documentation:

Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

🛣️ Future Scalability Roadmap
While the current monolithic architecture is highly optimized, the following upgrades are architecturally planned for enterprise-level scaling:

Asynchronous I/O: Transition from synchronous SQLAlchemy to aiomysql combined with AsyncSession to maximize FastAPI's event loop throughput.

Object Storage Integration: Decouple physical file uploads from the application server by migrating to AWS S3, enabling horizontal scaling across multiple load-balanced nodes.

Event-Driven Logging: Offload ActivityLog insertions from the main HTTP transaction thread to an asynchronous Message Queue (e.g., RabbitMQ or Kafka) to maintain ultra-low API latency.

Author: Nguyen Minh Hieu - B25DTCN240 - CNTT2