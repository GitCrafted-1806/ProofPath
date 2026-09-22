# ProofPath

> **"Don't just claim your skills. Prove them."**

ProofPath is an evidence-based campus placement verification platform designed to validate student technical skills through verifiable artifacts, deterministic evaluation rules, and practical assessments rather than self-reported resume claims.

---

## Live Demo

* **Placement Cell Dashboard:**  
  [https://proof-path-1r11ia88r-proof-path2.vercel.app](https://proof-path-1r11ia88r-proof-path2.vercel.app)

The web dashboard is the **College Placement Cell Dashboard** used by placement coordinators and TPOs to verify evidence, set company criteria, execute deterministic matching, and export candidate shortlists.

---

## Student Android App

* **Latest APK Download:**  
  [https://expo.dev/artifacts/eas/8OYDsfi2TBhA-N2WwNpgR6XuIxeegEAB6RACLoJ6HUM.apk](https://expo.dev/artifacts/eas/8OYDsfi2TBhA-N2WwNpgR6XuIxeegEAB6RACLoJ6HUM.apk)

The APK is the **Student Mobile Application** used by students to manage their profile, upload evidence, link GitHub project repositories, complete practical assessments, and view their public verification profile.

---

## Demo Credentials

> **Note:** These are pre-seeded demo accounts ready for evaluation without any registration needed.

* **Placement Cell (Coordinator):**
  * **Email:** `coordinator@college.edu`
  * **Password:** `Password123!`

* **Student:**
  * **Email:** `john.doe@nit.edu`
  * **Password:** `Password123!`

---

## Recommended Jury Walkthrough

1. **Open the Student Android App** on an Android phone (or emulator).
2. **Login as John Doe** (`john.doe@nit.edu` / `Password123!`).
3. **View the student dashboard** and claimed skills overview.
4. **Open a skill** (e.g., Python, Pandas, or Matplotlib) from the Skills tab to view its verification criteria.
5. **Connect/select the GitHub project** (`octocat-dev/analytics-pipeline`) to satisfy project evidence.
6. **Complete the practical assessment** for the skill.
7. **View the resulting deterministic verification status** (transiting to *Skill Assessed* or *Skill Verified*).
8. **Open the verification profile** (view the verifiable credential profile).
9. **Sign out** from the profile screen.
10. **Open the Placement Cell Dashboard** via the web link above.
11. **Login as the coordinator** (`coordinator@college.edu` / `Password123!`).
12. **Open Student Directory** and search for candidates.
13. **View John Doe's profile**, inspecting evidence files, GitHub repos, and skill verification states.
14. **Create or view a placement requirement** with eligible branches, minimum CGPA, and required skill levels.
15. **Demonstrate deterministic eligibility matching** (strict pass/fail rule evaluation without arbitrary scoring).
16. **Demonstrate assessment request / CSV export** for placement operations.

---

## Product Rules

* **Exactly Two Interfaces:** Dedicated **Student Mobile App** (React Native / Expo) and **College Placement Cell Dashboard** (Next.js web).
* **MVP Skills:** Python, Pandas, Matplotlib, Git/GitHub.
* **4 Verification Levels:**
  1. `UNVERIFIED`: Self-reported claim only.
  2. `EVIDENCE_SUPPORTED`: Verified certificate, project document, or GitHub repo attached.
  3. `SKILL_ASSESSED`: Passing score on practical skill assessment.
  4. `SKILL_VERIFIED`: Full multi-factor criteria met (evidence + practical assessment + code explanation / TPO verification).
* **Deterministic Rules Engine:** Final verification status is strictly determined by deterministic backend business logic.
* **No Direct AI Decision:** AI does not directly decide the final verification status; all verification is verifiable and rule-governed.
* **Strict Non-Ranking Rule:** Zero overall student ranking, leaderboard points, or arbitrary candidate scores.
* **GitHub Project Evidence:** GitHub is the authentic software-project evidence source.

---

## Architecture

* **Student Mobile App:** React Native + Expo + TypeScript
* **Placement Dashboard:** Next.js + TypeScript
* **Backend:** FastAPI + Python
* **Database:** PostgreSQL / Supabase in production; SQLite for local development
* **Deployment Pipeline:** Vercel (Web Dashboard) → Render (FastAPI Backend) → Supabase (Production DB)

---

## Security & Privacy

* **JWT Authentication:** Cryptographically signed stateless access tokens for all authenticated routes.
* **Role-Based Access Control (RBAC):** Strict isolation between `STUDENT` and `PLACEMENT_COORDINATOR` roles.
* **Student Ownership Isolation:** Students can access and modify only their own data; cross-student modifications are blocked with HTTP 403 Forbidden.
* **Private Backend & Database:** Uploaded evidence stored privately on disk with strict authorization gates.
* **No Secrets Committed:** Zero secrets or API keys committed to GitHub.
* **Deterministic Verification Rules:** Predictable, transparent verification rules ensuring placement trust and auditability.
