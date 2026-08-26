# QuizApp — AI-Powered Quiz & Learning Platform

QuizApp is a full-stack AI-powered learning platform for creating, importing, sharing, taking, and analyzing quizzes.

The platform combines traditional quiz functionality with AI-assisted quiz generation, document import, personalized performance analysis, an intelligent chatbot, analytics, mathematical answer validation, email verification, social discovery, and downloadable result reports.

🌐 **Live Application:** https://nurlanquiz.org

---

## ✨ Overview

QuizApp was built as a full-stack portfolio project focused on creating a modern learning experience powered by artificial intelligence.

Users can create quizzes manually or generate them with AI, import quiz content from documents, publish quizzes for others to discover, complete quizzes with multiple question types, review detailed results, track performance over time, and interact with an AI chatbot that understands their quiz activity and learning history.

The application includes a React/TypeScript frontend, a FastAPI/PostgreSQL backend, OpenAI-powered features, secure JWT authentication, email verification, analytics, PDF generation, cloud storage, automated testing, and production deployment.

---

## 🚀 Features

### Quiz Creation & Management

- Create quizzes manually
- Edit and delete owned quizzes
- Add quiz titles, descriptions, categories, and tags
- Public and unlisted quiz visibility
- Multiple question types
- Multiple-choice questions
- Written-answer questions
- Mathematical work questions
- AI-assisted quiz generation
- AI-assisted quiz icon selection
- Document-based quiz importing
- Shareable quiz links

### AI Quiz Generation & Import

QuizApp integrates OpenAI to assist with quiz creation and learning workflows.

Users can:

- Generate quiz content with AI
- Import quiz material from uploaded documents
- Extract and transform document content into structured quiz questions
- Generate relevant quiz metadata
- Receive AI-powered explanations and learning assistance
- Use AI to help categorize and represent quiz content

Document and image processing is supported through the backend import pipeline, with Pillow and multipart upload support for file handling.

### AI Learning Assistant

QuizApp includes an integrated AI chatbot designed specifically around the user's learning activity.

The chatbot supports:

- QuizApp feature and navigation questions
- Personalized quiz-performance questions
- Performance comparisons
- Question-level performance analysis
- Study recommendations
- Information about quizzes created by the user
- User connection and follow information
- Learning reports
- Context-aware responses based on application data
- Direct links to relevant areas of QuizApp
- Fast FAQ responses for common platform questions

The chatbot uses dedicated backend services for query interpretation, response generation, reporting, study recommendations, performance analysis, and application-data retrieval.

### Quiz Taking & Grading

Users can complete quizzes containing different kinds of questions.

QuizApp supports:

- Multiple-choice grading
- Written responses
- Mathematical work
- Deterministic mathematical validation using SymPy
- Math whiteboard input
- Stored whiteboard work
- Authenticated quiz attempts
- Guest quiz participation
- Detailed result pages
- Attempt history
- Repeated quiz attempts

Attempt history remains scoped to the authenticated user, including when taking quizzes created by another user.

### Results & Reports

After completing a quiz, users can review detailed performance information including:

- Score
- Correct and incorrect answers
- Question-level results
- AI-assisted explanations
- Previous attempts
- Quiz attempt history
- Performance data
- Downloadable PDF result reports

PDF generation is handled by ReportLab.

### Dashboard & Analytics

The personalized dashboard provides an overview of learning activity, including:

- Total quizzes created
- Quizzes taken
- Average score
- Recent quizzes
- Performance over time
- User score versus average performance
- Top quiz categories
- Category-level performance
- Links to continue learning and discover quizzes

Interactive frontend analytics are rendered using Recharts.

### Quiz Discovery

Public quizzes can be discovered through the global quiz library.

Discovery features include:

- Featured quizzes
- Paginated quiz browsing
- Search
- Category filtering
- Quiz metadata
- Creator information
- Attempt counts
- Public profile navigation

Unlisted quizzes remain accessible through their direct links without appearing in public discovery.

### Profiles & Social Features

QuizApp includes user profiles and lightweight social functionality.

Users can:

- View their own profile
- View public user profiles
- Browse another user's public quizzes
- Follow and unfollow users
- View follower/following information
- Navigate between creators and their quizzes

### Authentication & Account Security

Authentication is implemented with JWT-based access tokens and secure password hashing.

Account functionality includes:

- Registration
- Unique display names
- Email verification
- Six-digit email OTP codes
- OTP expiration
- OTP resend cooldown
- Maximum verification attempts
- Login
- Protected routes
- Password reset
- Password-reset verification
- Configurable access-token expiration
- Account settings

Passwords are securely hashed using Argon2.

### Email

QuizApp supports transactional email functionality for:

- Email verification
- OTP delivery
- Password-reset flows

Email credentials and sender information are configured through environment variables and are never stored in source control.

### Audit Logging

Important application activity is recorded through an audit system.

Audit events include actions such as:

- Quiz creation
- Quiz updates
- Quiz deletion
- Quiz completion

The application also provides an authenticated audit-log interface.

### Responsive UI

The frontend was designed as a modern responsive SaaS-style interface and supports:

- Desktop
- Tablet
- Mobile
- Light theme
- Dark theme
- System theme
- Responsive navigation
- Modals and confirmation dialogs
- Interactive charts
- Lucide icons

---

## 🧠 AI Architecture

AI functionality is separated into dedicated backend services instead of being embedded directly inside API routes.

The backend includes services for:

```text
ai_service
chatbot_service
chatbot_query_service
chatbot_response_service
chatbot_faq_service
chatbot_data_service
chatbot_created_quizzes_service
chatbot_performance_comparison_service
chatbot_question_performance_service
chatbot_study_recommendation_service
chatbot_user_connections_service
chatbot_report_service
chatbot_report_response_service
```

This separation keeps AI orchestration, application-data retrieval, reporting, recommendations, and response generation modular and testable.

---

## 🛠 Tech Stack

### Frontend

- React 19
- TypeScript
- Vite
- React Router
- Axios
- Recharts
- Lucide React
- SweetAlert2
- CSS
- Playwright
- ESLint

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Psycopg
- Alembic
- Pydantic
- JWT
- Argon2
- OpenAI API
- SymPy
- ReportLab
- Pillow
- Cloudinary
- SendGrid / Twilio email configuration
- Pytest
- pytest-xdist

### Infrastructure & Deployment

- Vercel — frontend hosting
- Render — backend hosting
- PostgreSQL — relational database
- Cloudinary — cloud media storage
- GitHub — source control and pull-request workflow
- Custom production domain — nurlanquiz.org

---

## 🏗 Architecture

```text
                         ┌──────────────────────┐
                         │      QuizApp UI      │
                         │ React + TypeScript   │
                         │        Vite          │
                         └──────────┬───────────┘
                                    │
                                    │ HTTPS / REST
                                    ▼
                         ┌──────────────────────┐
                         │     FastAPI API      │
                         │     /api/v1/*        │
                         └──────────┬───────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                    │
               ▼                    ▼                    ▼
      ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
      │   PostgreSQL   │   │    OpenAI      │   │   Cloudinary   │
      │ SQLAlchemy ORM │   │ AI Generation  │   │ Media Storage  │
      │    Alembic     │   │    Chatbot     │   │  Whiteboards   │
      └────────────────┘   └────────────────┘   └────────────────┘
                                    │
                                    ▼
                           ┌────────────────┐
                           │ Transactional  │
                           │     Email      │
                           └────────────────┘
```

---

## 📁 Project Structure

```text
quiz-app/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   ├── alembic.ini
│   └── requirements.txt
│
├── frontend/
│   ├── e2e/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── styles/
│   ├── package.json
│   ├── playwright.config.ts
│   ├── vercel.json
│   └── vite.config.ts
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔌 API

The FastAPI backend is organized under:

```text
/api/v1
```

Major API modules include:

```text
auth
quizzes
questions
attempts
users
dashboard
audit logs
AI
chatbot
```

A health endpoint is also available:

```text
GET /health
```

When running the backend locally, FastAPI's interactive API documentation is available at:

```text
http://localhost:8000/docs
```

---

## ⚙️ Local Development

### Prerequisites

Install:

- Python
- Node.js / npm
- PostgreSQL
- Git

Optional:

- Docker / Docker Compose

---

## 1. Clone the Repository

```bash
git clone https://github.com/NurlanRahimli/ai-quiz-platform.git
cd ai-quiz-platform
```

---

## 2. Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Return to the project root when needed:

```bash
cd ..
```

---

## 3. Environment Variables

Create a `.env` file in the project root.

Example:

```env
POSTGRES_DB=quiz_app
POSTGRES_USER=quiz_user
POSTGRES_PASSWORD=your_postgres_password

DATABASE_URL=postgresql+psycopg://quiz_user:your_postgres_password@localhost:5432/quiz_app

JWT_SECRET_KEY=replace_with_a_secure_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173

EMAIL_OTP_EXPIRE_MINUTES=10
EMAIL_OTP_RESEND_COOLDOWN_SECONDS=60
EMAIL_OTP_MAX_ATTEMPTS=5

OPENAI_API_KEY=your_openai_api_key

CLOUDINARY_URL=your_cloudinary_url

TWILIO_API_KEY_SID=your_twilio_api_key_sid
TWILIO_API_KEY_SECRET=your_twilio_api_key_secret
TWILIO_FROM_EMAIL=no-reply@nurlanquiz.org
TWILIO_FROM_NAME=QuizApp
```

Never commit real production secrets to Git.

---

## 4. Database Migrations

With the backend virtual environment activated:

```bash
cd backend
alembic upgrade head
```

---

## 5. Start the Backend

From `backend/`:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

## 6. Frontend Setup

In another terminal:

```bash
cd frontend
npm install
```

Create:

```text
frontend/.env
```

with:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

Start the frontend:

```bash
npm run dev
```

The development application will normally be available at:

```text
http://localhost:5173
```

---

## 🧪 Testing

### Backend

QuizApp contains an extensive backend pytest suite covering authentication, quizzes, questions, attempts, grading, AI functionality, chatbot behavior, dashboard data, email services, audit logs, PDF generation, users, imports, and mathematical validation.

Run the complete backend test suite:

```bash
cd backend
pytest -q
```

For substantially faster execution on multi-core machines, QuizApp includes `pytest-xdist`:

```bash
pytest -q -n auto
```

At the time of the latest project validation:

```text
533 tests passed
```

### Run a Specific Test File

```bash
pytest tests/test_attempts.py -q
```

### Run a Specific Test

```bash
pytest tests/test_attempts.py::test_name -q
```

---

## 🎭 End-to-End Testing

Frontend authentication flows are tested with Playwright.

From `frontend/`:

```bash
npm run test:e2e
```

---

## 🔍 Frontend Validation

Run ESLint:

```bash
npm run lint
```

Create a production build:

```bash
npm run build
```

---

## 🚢 Deployment

### Frontend

The React/Vite frontend is deployed through Vercel and configured for SPA routing.

Production:

```text
https://nurlanquiz.org
```

### Backend

The FastAPI backend is deployed on Render.

Production environment variables are configured through Render rather than committed to the repository.

The backend provides:

```text
GET /health
```

for health monitoring.

### Database

Production uses PostgreSQL with schema changes managed through Alembic migrations.

---

## 🔐 Security

QuizApp includes several security measures:

- Argon2 password hashing
- JWT authentication
- Token expiration
- Protected API routes
- Ownership authorization
- User-scoped attempt data
- Email verification
- Expiring OTP codes
- OTP attempt limits
- OTP resend cooldowns
- Password-reset verification
- CORS configuration
- Environment-based secret management
- Server-side quiz grading
- Hidden correct answers during quiz-taking flows

Sensitive credentials are never intended to be stored in source control.

---

## 🧮 Mathematical Questions

Mathematical answers use SymPy-based validation and grading rather than relying exclusively on AI.

This allows QuizApp to compare mathematically equivalent expressions deterministically when appropriate.

The quiz-taking interface also supports mathematical work and a whiteboard experience for showing work before submitting a final answer.

---

## 📄 PDF Reports

Quiz results can be exported as PDF reports.

The backend uses ReportLab to generate downloadable result documents containing quiz and performance information.

---

## 🗄 Database Models

Core application models include:

- User
- Quiz
- Question
- Answer Choice
- Quiz Attempt
- Quiz Attempt Answer
- User Follow
- Email Verification
- Password Reset
- Audit Log

Database schema changes are managed with Alembic migrations.

---

## 🌐 Production

**QuizApp:** https://nurlanquiz.org

The production architecture separates the frontend, API, database, AI integrations, transactional email, and cloud media storage while keeping configuration environment-specific.

---

## 👨‍💻 Author

**Nurlan Rahimli**

Built as a full-stack AI software engineering portfolio project using React, TypeScript, FastAPI, PostgreSQL, and OpenAI.

---

## 📜 License

This project is currently provided as a portfolio project. No open-source license has been specified.
