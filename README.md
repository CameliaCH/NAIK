# NAIK — Naikkan Taraf Hidup Anda

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://naik.onrender.com)

🚀 **Live demo:** [naik.onrender.com](https://naik.onrender.com)

**Malaysia's free AI-powered career platform for the 4.86 million women outside our workforce.**

NAIK ("rise" in Malay) is built for the women who fall through the cracks of mainstream career tools — particularly those re-entering the workforce after a caregiving break. We turn years of household management into professional language, give women the confidence to walk into interviews, and surface the jobs, skills, and grants that actually fit their lives.

> 🚧 *Live demo coming soon — see screenshots below.*

---

## Why NAIK Exists

According to the Department of Statistics Malaysia, **4.86 million Malaysian women are currently outside the labour force** — nearly 70% of all non-working Malaysians. Most want to return, but face platforms that treat their caregiving years as a "gap" rather than experience.

Society calls it a career gap.
**We call it experience that hasn't been translated yet.**

NAIK is built to change that.

---

## Features

| Feature | Description |
|---|---|
| **Career Quiz** | 5-question assessment that maps interests, flexibility, and caregiving responsibilities to job categories |
| **Job Recommendations** | Top 3 personalised matches with a "why this fits you" explanation powered by AI |
| **Job Explorer** | Browse and save jobs from a curated library with salary bands and progression timelines |
| **CV Builder** | Step-by-step CV wizard with AI composition — turns raw, everyday descriptions into polished bullet points |
| **Caregiving Translator** | Reframes childcare, home management, and family responsibilities as transferable professional skills |
| **Confidence Builder** | Voice-powered AI interview coach that role-plays the hardest employment-gap questions |
| **Community & Connect** | Social feed, community posts with replies and likes, and a mentor-request system |
| **Ibu Mentor Finder** | Matches users with experienced mentors for career guidance |
| **Resources** | WhatsApp message templates, Malaysian women's legal rights at work, and safe gig-work checklist |
| **Subsidy Finder** | Curated Malaysian government training grants and funding |
| **Multilingual** | Full UI and AI responses in English, Bahasa Melayu, and Mandarin Chinese |

---

## How It Works
User → Flask App → Supabase (data, auth, storage)
↓
Groq API (LLM + Whisper STT)
↓
D-ID API (avatar video, optional)
↓
Personalised CV · Interview Coaching · Career Roadmap

A returning woman takes a 3-minute quiz → gets matched to 3 jobs → unlocks a personalised roadmap → builds her CV with AI translating her caregiving years into professional language → practises interviews with a voice AI → connects with mentors and a community of women on the same journey.

---

## Tech Stack

### Backend
- **[Flask](https://flask.palletsprojects.com/)** — Python web framework
- **[Supabase](https://supabase.com/)** — PostgreSQL database, authentication, and file storage
- **[Passlib / Argon2](https://passlib.readthedocs.io/)** — password hashing

### Frontend
- **Jinja2** — server-side templating
- **Vanilla JavaScript** — no frontend framework or build step required
- **Custom CSS** — responsive, mobile-first design with CSS custom properties

### AI & External Services
- **[Groq](https://groq.com/)** — LLM inference
  - `llama-3.3-70b-versatile` — CV composition
  - `llama-3.1-8b-instant` — CV translation, interview coaching
  - `whisper-large-v3` — speech-to-text transcription (auto-detects English / Malay / Mandarin)
- **[D-ID](https://www.d-id.com/)** — talking avatar video generation for interview feedback

### Internationalisation
- JSON translation files for `en`, `ms`, `zh`
- Session-based language switcher; AI outputs match the active language

---

## Project Structure

---
NAIK/
├── app.py                       # Main Flask application & all API routes
├── db.py                        # Supabase client singleton
├── roadmap_backend.py           # Quiz scoring & job-matching engine
├── blueprints/
│   └── interview.py             # Interview coaching routes
├── services/
│   ├── avatar_service.py        # D-ID avatar video generation
│   ├── cv_builder_service.py    # AI CV composition (Groq)
│   ├── cv_translator_service.py # Everyday language → CV language (+ caregiving mode)
│   ├── llm_service.py           # Interview coaching AI
│   └── stt_service.py           # Groq Whisper transcription
├── templates/                   # Jinja2 HTML templates
│   ├── base.html                # Shared layout, nav, dark mode, onboarding island
│   ├── NAIK.html                # Homepage
│   ├── signIn.html              # Login / sign-up
│   ├── profile.html             # Editable user profile
│   ├── explore.html             # Job discovery
│   ├── roadmap.html             # Career quiz
│   ├── recommendations.html     # Top 3 job matches
│   ├── skills.html              # Skill tracking dashboard
│   ├── interview.html           # Confidence Builder
│   ├── cv_builder.html          # CV Builder & Caregiving Translator
│   ├── connect.html             # Community feed & mentor requests
│   ├── match.html               # Ibu Mentor finder
│   ├── resources.html           # Resources hub
│   ├── subsidy.html             # Subsidy finder
│   ├── roadmap_view.html        # Saved career roadmap
│   └── profile_view.html        # Public user profile
├── static/
│   ├── naik.css                 # Global styles
│   ├── naik.js                  # Homepage interactivity
│   ├── roadmap.js               # Quiz & job explorer logic
│   ├── js/
│   │   └── interviewer.js       # Interview coach (recording, TTS, AI)
│   └── images/                  # UI graphics and partner logos
├── translations/
│   ├── en.json
│   ├── ms.json
│   └── zh.json
├── requirements.txt             # Python dependencies
└── .env                         # API keys (see Environment Variables below)
---

## Getting Started

### Prerequisites

- Python 3.10+
- A [Supabase](https://supabase.com/) project (free tier works)
- A [Groq](https://console.groq.com/) API key (free tier works)
- A [D-ID](https://www.d-id.com/) API key (required only for avatar video — the rest of the interview coach works without it)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/CameliaCH/NAIK.git
cd NAIK

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
# Flask
SECRET_KEY=your-random-secret-key-at-least-32-characters

# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-jwt-key

# Groq (LLM + Whisper)
GROQ_API_KEY=gsk_your-groq-api-key

# D-ID (avatar video — optional)
DID_API_KEY=your-did-api-key
```

> `SUPABASE_SERVICE_KEY` is the **service role** key (not the anon key) — found in your Supabase project under Settings → API.

### Running Locally

```bash
flask --app app run --debug --port 5001
```

Open [http://localhost:5001](http://localhost:5001) in your browser.

---

## Database Schema

NAIK uses Supabase (PostgreSQL). The key tables are:

| Table | Purpose |
|---|---|
| `users` | Accounts, profile data, avatar URL, public saved jobs |
| `jobs` | Job listings with bilingual titles, salary bands, category tags |
| `quiz_responses` | User quiz answers (JSON) |
| `saved_jobs` | Many-to-many: users ↔ jobs |
| `community_posts` | Social feed posts with image support |
| `community_likes` | Post likes (one per user per post) |
| `community_replies` | Threaded replies on posts |
| `mentor_requests` | User-initiated mentor connection requests |

---

## API Reference

### Authentication
| Method | Route | Description |
|---|---|---|
| POST | `/auth/signup` | Create a new account |
| POST | `/auth/login` | Email + password login |
| GET | `/auth/logout` | Sign out |

### Profile
| Method | Route | Description |
|---|---|---|
| POST | `/auth/profile/update` | Update name, headline, bio, etc. |
| POST | `/auth/profile/avatar` | Upload profile photo |
| GET | `/u/<user_id>` | View a public profile |

### Quiz & Jobs
| Method | Route | Description |
|---|---|---|
| POST | `/api/quiz/save` | Save quiz answers |
| GET | `/api/quiz/results` | Retrieve quiz results + saved job IDs |
| GET | `/api/jobs/all` | Full job library |
| POST | `/api/jobs/save` | Save a job |
| POST | `/api/jobs/unsave` | Remove a saved job |
| POST | `/api/jobs/why-fit` | AI explanation of why a job fits the user |
| POST | `/api/recommendations` | Top 3 personalised job matches |

### CV
| Method | Route | Description |
|---|---|---|
| POST | `/cv-builder/translate` | Everyday experience → CV bullet point |
| POST | `/cv-builder/translate-caregiving` | Caregiving years → professional skills |
| POST | `/professional-me/build` | Compose a full CV from structured input |

### Interview Coach
| Method | Route | Description |
|---|---|---|
| POST | `/interview/transcribe` | Transcribe voice recording to text |
| POST | `/interview/respond` | Get AI coaching response |
| POST | `/interview/avatar` | Generate avatar feedback video |
| POST | `/interview/reset` | Clear session history |

### Community
| Method | Route | Description |
|---|---|---|
| GET | `/api/connect/posts` | Community feed |
| POST | `/api/connect/posts` | Create a post |
| POST | `/api/connect/posts/<id>/like` | Like / unlike a post |
| POST | `/api/connect/posts/<id>/replies` | Reply to a post |
| POST | `/api/mentor/request` | Send a mentor request |

---

## Multilingual Support

The UI is available in three languages, switchable at any time:

| Code | Language |
|---|---|
| `en` | English |
| `ms` | Bahasa Melayu |
| `zh` | Mandarin Chinese (普通话) |

Switch via the language selector in the nav, or by visiting `/set-lang?lang=ms`. The active language is stored in the session and all AI responses — interview coaching, CV translation — are generated in the same language.

---

## Design Decisions

**No frontend framework.** Jinja2 + vanilla JS keeps the stack simple, fast to load on mobile data connections, and easy for contributors to understand without a build step.

**Caregiving as work.** The CV translator and interview coach are built around the premise that caregiving years are real professional experience. The AI prompts explicitly reframe home management, child development, and healthcare coordination as transferable workplace skills.

**Voice-first interview practice.** The interview coach uses the Web Speech API for text-to-speech and Groq Whisper for transcription so users can practise speaking out loud, not just typing.

**Language is explicit, not inferred.** Rather than asking the AI to guess the output language from the input text (which fails in a multilingual context), the active UI language is passed explicitly to every AI call so the response is always consistent with what the user chose.

---

## Known Limitations & Future Work

- Avatar video generation (D-ID) requires a paid API key for production scale
- Mandarin AI responses occasionally fall back to English under high token loads
- Currently optimised for desktop and mobile web — no native app yet
- Job listings are curated rather than scraped (planned: integration with JobStreet API)
- Mentor matching is currently manual (planned: AI-driven matching based on quiz responses + mentor profiles)
- Subsidy data is hand-curated (planned: live integration with PADU and government grant portals)

---

## Contributing

Pull requests are welcome. For significant changes, please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a pull request

---

## Acknowledgements

- Built by **Team Unemployeds** for the National AI Competition (NAIC) 2026
- Designed for the 4.86 million Malaysian women re-entering the workforce after a caregiving break
- Powered by [Groq](https://groq.com/), [Supabase](https://supabase.com/), and [D-ID](https://www.d-id.com/)
- Data sources: Department of Statistics Malaysia (DOSM) Labour Force Survey 2024 & Q4 2025
- Fonts: [Playfair Display](https://fonts.google.com/specimen/Playfair+Display) + [Plus Jakarta Sans](https://fonts.google.com/specimen/Plus+Jakarta+Sans)

---

*NAIK — Naikkan Taraf Hidup Anda. **She rises. So does Malaysia.***
