# Pronunciation Adventure 🎙️

An interactive English pronunciation platform designed for students. Pronunciation Adventure features a layered architecture designed for high maintainability, strict security, and smooth user experience.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER (Streamlit Multipage Pages & UI)     │
│ - app.py (Entrypoint & Session Sync)                    │
│ - pages/1_Login.py, 2_Signup.py, 3_Profile.py           │
│ - pages/4_Level_Dev.py, 5_Play.py, 6_Mic_Test.py        │
├─────────────────────────────────────────────────────────┤
│ APPLICATION / SERVICE LAYER (Pure Python Business Logic)│
│ - services/auth_service.py (Auth & Sessions)            │
│ - services/progression_service.py (Level/World Queues)  │
│ - services/scoring_service.py (Phonetic & RapidFuzz)    │
│ - services/speech_service.py (Web Speech & Fallback)    │
│ - services/override_service.py (Teacher Overrides)      │
├─────────────────────────────────────────────────────────┤
│ REPOSITORY / DATA ACCESS LAYER                          │
│ - repositories/supabase_client.py (Cached Anon Client)  │
│ - repositories/profiles_repo.py (Profiles DB Access)    │
│ - repositories/content_repo.py (Curriculum DB Access)   │
│ - repositories/progress_repo.py (Progress DB Access)    │
│ - repositories/attempts_repo.py (Attempts DB Access)    │
├─────────────────────────────────────────────────────────┤
│ SUPABASE POSTGRESQL + STORAGE + AUTH                    │
│ - profiles, override_audit_log (Phase 1)                │
│ - worlds, levels, words, level_words (Phase 2)          │
│ - student_progress, world_progress, word_progress (P3)  │
│ - word_attempts (Phase 6)                               │
│ - Storage Bucket: word-images                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Setup & Installation

### 1. Python Version & Virtual Environment
This project is officially supported and pinned to **Python 3.11** (e.g. Python 3.11.9) for optimal compatibility with Streamlit, PyArrow, Pandas, and Supabase.

Create and activate a clean isolated virtual environment:

```bash
# Windows
py -3.11 -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Secrets
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and populate your credentials:
```toml
# Required for Streamlit Web Application (Uses only anon key; strict RLS enforced):
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"

# SHA-256 hash of the Teacher/Admin password used for authorized word overrides.
# Default dev password is 'teacher123'
TEACHER_OVERRIDE_HASH = "cde383eee8ee7a4400adf7a15f716f179a2eb97646b37e089eb8d6d04e663416"

# (Developer / Offline Seeding Only - NEVER used in runtime app code)
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key-here"
```

### 4. Configure Supabase Database Schema
Run migrations in sequence in your Supabase SQL Editor:
1. `db/migrations/001_init_auth_and_profiles.sql`
2. `db/migrations/002_content_schema.sql`
3. `db/migrations/003_progression.sql`
4. `db/migrations/004_word_attempts.sql`

### 5. Seed Development Curriculum & Upload Images (Offline Developer Tools)
```bash
# Validate 42-word development curriculum
python scripts/validate_content.py

# Seed worlds, levels, words, and level_words into Supabase (Requires SUPABASE_SERVICE_ROLE_KEY)
python scripts/seed_content.py

# (Optional) Upload curated word images to Supabase Storage
python scripts/upload_images_to_storage.py
```

### 6. Run Automated Tests
```bash
pytest tests/ -v
```

### 7. Launch the Streamlit App
```bash
streamlit run app.py
```

---

## 🔒 Security & Data Integrity

- **Stateless Anon Client:** Repositories communicate strictly using the Supabase `anon` key.
- **Strict Row-Level Security (RLS):** Policies ensure authenticated users can only view and update their own records (`student_id = auth.uid()`).
- **Trigger-Enforced Role Security:** Prevents self-escalation of the `role` column.
- **HTML Sanitization:** All dynamic user inputs are escaped (`html.escape()`) to prevent XSS.
