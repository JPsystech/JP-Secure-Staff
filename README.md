# JP Secure Staff

Full-stack staff management system built with Next.js, FastAPI, PostgreSQL, and MinIO.

## Tech Stack

- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + shadcn/ui + lucide-react
- **Backend**: FastAPI + SQLAlchemy + Alembic + Pydantic
- **Database**: PostgreSQL
- **File Storage**: MinIO (S3 compatible)
- **Authentication**: JWT + RBAC permissions

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

5. Update `.env` with your database credentials and other settings.

6. Create database:
```bash
createdb jp_secure_staff
```

7. Run migrations:
```bash
alembic upgrade head
```

8. Seed initial data:
```bash
python scripts/seed_data.py
```

9. Start the server:
```bash
python run.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file:
```bash
cp .env.local.example .env.local
```

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Default Login Credentials

After seeding data, you can use these credentials:

- **Master Admin**: admin@jpsecure.com / admin123
- **Finance**: finance@jpsecure.com / finance123
- **HR**: hr@jpsecure.com / hr123
- **Operations**: ops@jpsecure.com / ops123

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Core config, database, security
│   │   ├── models/       # SQLAlchemy models
│   │   └── schemas/      # Pydantic schemas
│   ├── alembic/          # Database migrations
│   └── scripts/          # Utility scripts
└── frontend/
    ├── app/              # Next.js app router pages
    ├── components/       # React components
    └── lib/              # Utilities and API client
```

## Development Phases

### Phase 0: Auth + Route Guards ✅
- [x] Backend auth endpoints
- [x] Frontend login pages
- [x] Route guards
- [x] UserShell and AdminShell

### Phase 1: Master Admin Setup (In Progress)
- [ ] Departments CRUD
- [ ] Roles & Permissions
- [ ] Users Management
- [ ] Master Data
- [ ] Policies
- [ ] Templates

