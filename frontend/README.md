# Assignment Evaluator Frontend

Teacher UI for evaluating student code and content submissions.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Language**: TypeScript
- **State**: React Hooks

## Features

- ✅ Clean, responsive teacher interface
- ✅ File upload page for submissions
- ✅ Results dashboard with scoring
- ✅ No authentication (teacher-only setup)
- ✅ Tailwind CSS styling
- ✅ Mobile-responsive design

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx           # Home page
│   │   ├── layout.tsx         # Root layout
│   │   ├── globals.css        # Tailwind globals
│   │   ├── upload/
│   │   │   └── page.tsx       # Upload page
│   │   └── results/
│   │       └── page.tsx       # Results page
│   └── components/            # Reusable components
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── postcss.config.ts
```

## Getting Started

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
npm run build
npm start
```

## Pages

### Home Page (`/`)
- Welcome screen with navigation
- Links to Upload and Results pages

### Upload Page (`/upload`)
- Select assignment type (Code, Content, or Mixed)
- Provide problem statement or ideal reference
- Upload student submission files
- (TODO) Send to backend API

### Results Page (`/results`)
- View evaluation results for all students
- Summary statistics (average, highest, lowest scores)
- Individual student scores and feedback
- Status badges and visual indicators
- (TODO) Load results from backend
- (TODO) CSV export

## Backend Connection

Backend API endpoints to integrate:
- `POST /api/evaluate` - Submit files for evaluation

(Not connected yet - placeholder UI only)

## Styling

- **Framework**: Tailwind CSS v3
- **Colors**: Indigo/Blue primary theme
- **Responsive**: Mobile-first design
- **Components**: Cards, forms, buttons, badges

## Notes

- No authentication required (teacher-only setup)
- Frontend is currently disconnected from backend
- All results shown are sample/placeholder data
