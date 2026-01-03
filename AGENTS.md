# AGENTS.md - AI Coding Agent Guidelines

This document provides coding standards and commands for AI agents working on the PolyLearner codebase.

## Project Overview

PolyLearner is a full-stack AI-powered productivity application with:
- **Backend**: Python/FastAPI with configurable database (MongoDB or Google Firestore)
- **Frontend**: React/TypeScript with Vite, Tailwind CSS, shadcn/ui components
- **Mobile**: Flutter/Dart with Material Design
- **Database**: Abstraction layer supporting MongoDB (Motor async driver) and Google Firestore
- **LLM Integration**: Multi-provider support (OpenAI, Anthropic, Ollama, custom)
- **Features**: Task management, goal tracking, AI coaching, smart scheduling, Google Calendar integration

## Build, Lint & Test Commands

### Backend (Python/FastAPI)
```bash
# Development (with auto-reload)
cd app && uvicorn app:app --reload

# Production
cd app && python app.py

# Docker (recommended)
docker compose up --build

# Install dependencies
pip install -r app/requirements.txt

# No test framework configured yet (pytest recommended for future)
```

### Frontend (React/TypeScript/Vite)
```bash
# Development server (port 8080)
cd web && npm run dev

# Production build
cd web && npm run build

# Development build
cd web && npm run build:dev

# Lint
cd web && npm run lint

# Preview production build
cd web && npm run preview

# Install dependencies
cd web && npm install

# No test framework configured
```

### Mobile (Flutter/Dart)
```bash
# Run app
cd mobile && flutter run

# Build
cd mobile && flutter build apk  # Android
cd mobile && flutter build ios  # iOS

# Lint
cd mobile && flutter analyze

# Test (framework available, no tests yet)
cd mobile && flutter test

# Install dependencies
cd mobile && flutter pub get
```

### Docker Compose
```bash
# Start all services (app, mongo, ollama)
docker compose up --build

# Stop all services
docker compose down

# View logs
docker compose logs -f app
```

## Code Style Guidelines

### Python (Backend)

#### Imports
- Standard library first, then third-party, then local imports
- Use absolute imports for local modules
```python
from datetime import datetime
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from models import Task, User
```

#### Formatting
- 4 spaces for indentation (no tabs)
- Class names: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Max line length: ~120 characters (soft limit)
- Docstrings: Triple-quoted strings for modules/classes/functions

#### Types & Models
- Use Pydantic `BaseModel` for all request/response models
- Use Python type hints extensively: `def func(name: str, count: int) -> bool:`
- Use `Optional[T]` for nullable types
- Enums for fixed value sets: `class TaskCategory(str, Enum):`
- Field validation with Pydantic: `Field(..., ge=1, le=10)`

#### Error Handling
- Raise `HTTPException` for API errors: `raise HTTPException(status_code=404, detail="Not found")`
- Use try/except for database operations
- Log errors with `logger.error()`
- Return meaningful error messages in responses

#### Async/Await
- Use `async def` for all FastAPI route handlers
- Use `await` for MongoDB operations (Motor)
- Use `await` for HTTP requests (httpx)
- Pattern: `async def get_tasks() -> List[Task]:`

#### Database (MongoDB)
- Use Motor async driver
- Collections: `db["tasks"]`, `db["goals"]`, etc.
- Auto-increment IDs: Use counters collection
- Field names: `snake_case` (e.g., `created_at`, `user_id`)

### TypeScript/React (Frontend)

#### Imports
- React imports first, then third-party, then local (components, contexts, lib, types)
- Use path aliases: `@/components/ui/button` instead of relative paths
```typescript
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { getTasks, Task } from "@/lib/api";
```

#### Formatting
- 2 spaces for indentation
- Component names: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE` or `camelCase`
- Interfaces: `PascalCase` (no `I` prefix)
- Semicolons: Optional (current codebase omits them)

#### Types & Interfaces
- Define interfaces for all data structures
- Use TypeScript type annotations everywhere
- Export interfaces from `@/lib/api.ts` for shared types
- Use union types for enums: `category: 'research' | 'coding' | 'admin' | 'networking'`

#### Components
- Use functional components with hooks
- Props: Define interface for component props
- State: Use `useState`, `useEffect` hooks
- Pattern: `export default function ComponentName() { ... }`
- Destructure props in function params

#### Error Handling
- Use try/catch for async operations
- Log errors: `console.error('Failed to load tasks:', err)`
- Show user-friendly error messages (toast notifications)
- Provide fallback UI for loading/error states

#### API Calls
- Use `@/lib/api.ts` client functions
- Always include auth headers: `getAuthHeaders()`
- Handle loading states with local state
- Handle errors gracefully with user feedback
- Use React Query for server state management (already configured)

#### UI Components
- Use shadcn/ui components from `@/components/ui/`
- Use Tailwind CSS for styling
- Follow existing design system (colors, spacing, typography)
- Dark theme support via `next-themes`

### Dart/Flutter (Mobile)

#### Formatting
- 2 spaces for indentation
- Class names: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `lowerCamelCase` (Dart convention)
- File names: `snake_case.dart`

#### Widgets
- Use `const` constructors where possible
- StatelessWidget for static UI
- StatefulWidget for dynamic UI
- Extract reusable widgets into separate files

## Environment Variables

### Backend (.env)
```bash
# Database Configuration
DB_TYPE=mongodb  # or firestore
MONGO_URI=mongodb://mongo:27017
MONGO_DB=polylearner
FIRESTORE_PROJECT_ID=your-gcp-project-id  # if using Firestore
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json  # if using Firestore

# LLM Configuration
LLM_PROVIDER=ollama  # or openai, anthropic, custom
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_BASE_URL=http://ollama:11434

# Authentication
GOOGLE_CLIENT_ID=...
JWT_SECRET=your-secret-key-change-in-production
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=...
```

## Architecture Patterns

### Backend
- FastAPI async routes with Pydantic models
- JWT authentication via `Authorization: Bearer <token>`
- Database abstraction layer supporting MongoDB (Motor) and Firestore
- Service layer pattern: `analytics_service.py`, `calendar_service.py`, etc.
- Multi-provider LLM abstraction in `llm_provider.py`
- Database factory pattern in `database_factory.py`

### Frontend
- React Router for navigation
- Context API for auth state (`AuthContext`)
- React Query for server state
- Component-based architecture with shadcn/ui
- API client layer in `@/lib/api.ts`

### Mobile
- Bottom navigation pattern
- Screens in `lib/screens/`
- Dark theme configuration in `lib/theme/`

## Common Patterns

### Adding a New API Endpoint
1. Define Pydantic models in `app/models.py`
2. Add route handler in `app/app.py` or service file
3. Update `web/src/lib/api.ts` with TypeScript interface and function
4. Use in React components

### Adding a New UI Component
1. Use shadcn/ui base components from `@/components/ui/`
2. Create custom components in `@/components/` or `@/components/dashboard/`
3. Follow Tailwind CSS styling patterns
4. Ensure responsive design

### Database Operations
- Use `await db.collection.find_one()` for single document
- Use `await db.collection.find().to_list()` for multiple documents
- Use `await db.collection.insert_one()` for creation
- Use `await db.collection.update_one()` for updates
- Handle `None` results appropriately
- Database abstraction layer automatically handles MongoDB vs Firestore

## ESLint Configuration
- TypeScript ESLint enabled
- React Hooks rules enforced
- React Refresh for HMR
- Unused vars warnings disabled (`@typescript-eslint/no-unused-vars: off`)

## TypeScript Configuration
- Path aliases enabled: `@/*` maps to `./src/*`
- Relaxed strictness: `noImplicitAny: false`, `strictNullChecks: false`
- Skip lib check enabled for faster compilation

## Documentation Files
- `ANALYTICS_SERVICE.md` - Analytics implementation details
- `CALENDAR_PERMISSIONS.md` - Google Calendar integration guide
- `GOAL_ONBOARDING_WORKFLOW.md` - Goal onboarding flow
- `VECTOR_EMBEDDINGS_AND_CALENDAR.md` - Vector embeddings documentation
- `DATABASE_SETUP.md` - Database configuration and Firestore setup
- `DATABASE_ABSTRACTION_SUMMARY.md` - Database abstraction layer details
- `requirements.md` - System requirements and rules
- `GOAL_ONBOARDING_WORKFLOW.md` - Goal onboarding flow
- `VECTOR_EMBEDDINGS_AND_CALENDAR.md` - Vector embeddings documentation
- `requirements.md` - System requirements and rules

## Notes for AI Agents
- Always read existing code before making changes
- Follow established patterns in the codebase
- Test changes locally before committing
- Maintain consistency with existing code style
- Update documentation when adding new features
- No test frameworks configured yet - add tests when implementing new features
- Use Docker Compose for development to ensure all services run correctly
