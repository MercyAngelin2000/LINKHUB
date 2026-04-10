"# LINKHUB" 
1.  Clone Repository
Backend Setup (FastAPI)
cd backend

# Create virtual environment
python -m venv venv

# Activate environment
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload

Environment Variables
Backend .env
DATABASE_URL=postgresql://user:password@localhost:5432/linkhub

Database Setup
Install PostgreSQL
Create database:
CREATE DATABASE linkhub;
Update your DATABASE_URL accordingly

| Method | Endpoint        | Description         |
| ------ | --------------- | ------------------- |
| GET    | /links/{tenant} | Get links by tenant |
| POST   | /links          | Create new link     |
| POST   | /click/{id}     | Track link click    |


Key Decisions
FastAPI used for performance and simplicity

Multi-tenant handled via query parameter

Clean UI built using Tailwind CSS

Smooth animations using Framer Motion

Cloud deployment using free-tier services
