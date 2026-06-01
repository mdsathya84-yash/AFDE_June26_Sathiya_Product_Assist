# AI-Powered Product Strategy Assistant

A full-stack AI application that ingests business sales data, runs six parallel LangGraph agents to generate strategic insights, and delivers an interactive React dashboard with chat and PDF report capabilities.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11+) |
| AI Orchestration | LangGraph (parallel multi-agent) |
| LLM Primary | OpenAI gpt-4o-mini |
| LLM Fallback | Groq llama-3.3-70b-versatile |
| Vector Store | ChromaDB + Hybrid Search (Dense + BM25 + RRF) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Charts | Recharts |
| State Management | Zustand |
| PDF Reports | WeasyPrint + Jinja2 |

---

## Project Structure

```
product-strategy-assistant/
├── backend/
│   ├── agents/                         # 6 LangGraph agents
│   │   ├── customer_insights_agent.py
│   │   ├── sales_analysis_agent.py
│   │   ├── swot_agent.py
│   │   ├── feature_prioritization_agent.py
│   │   ├── opportunity_scoring_agent.py
│   │   ├── strategy_recommendation_agent.py
│   │   ├── graph.py                    # LangGraph StateGraph orchestration
│   │   ├── state.py                    # AgentState TypedDict
│   │   └── utils.py                    # JSON extraction utility
│   ├── api/
│   │   └── routes.py                   # FastAPI endpoints
│   ├── core/
│   │   ├── config.py                   # Pydantic settings
│   │   ├── llm_router.py               # OpenAI → Groq failover router
│   │   ├── vector_store.py             # ChromaDB + HybridSearchRetriever
│   │   └── report_generator.py         # WeasyPrint PDF generator
│   ├── ingestion/
│   │   ├── csv_parser.py               # CSV → documents + aggregates
│   │   ├── text_splitter.py            # RecursiveCharacterTextSplitter
│   │   └── ingestor.py                 # Ingestion pipeline orchestrator
│   ├── models/
│   │   └── schemas.py                  # Pydantic request/response models
│   ├── templates/
│   │   └── report.html                 # Jinja2 PDF report template
│   └── main.py                         # FastAPI app entry point
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx           # KPI cards + Recharts visualizations
│   │   │   ├── Chat.tsx                # Interactive chat with agent outputs
│   │   │   └── Report.tsx              # Report viewer + PDF/JSON download
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── AgentCard.tsx
│   │   │   ├── SWOTGrid.tsx
│   │   │   ├── RICETable.tsx
│   │   │   └── OpportunityCard.tsx
│   │   ├── store/
│   │   │   └── useAnalysisStore.ts     # Zustand global state
│   │   └── api/
│   │       └── client.ts               # Axios API wrappers
│   ├── package.json
│   └── vite.config.ts
├── sample_data/
│   └── Sample_Sales_Data.csv           # 120 rows, 10 products, Jan–Apr 2026
├── requirements.txt
├── docker-compose.yml
├── application.md                       # Full architecture documentation
└── .env.example
```

---

## Agent Architecture

```
retrieve_context (hybrid search)
        │
        ├──→ Customer Insights Agent  ──────────┐
        ├──→ Sales Analysis Agent     ──────────┤
        ├──→ SWOT Analysis Agent      ──────────┼──→ Strategy Recommendation → Report Assembly
        ├──→ Feature Prioritization   ──────────┤
        └──→ Opportunity Scoring      ──────────┘
                  (5 agents run in parallel)
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/mdsathya84-yash/AFDE_June26_Sathiya_Product_Assist.git
cd AFDE_June26_Sathiya_Product_Assist
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your API keys:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://your-gateway.com/v1   # optional custom gateway
GROQ_API_KEY=your_groq_api_key                # optional fallback
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the backend

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

The server auto-ingests `sample_data/Sample_Sales_Data.csv` on first startup.

### 5. Install and run the frontend (development)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**, proxying `/api/*` to the backend.

### 6. Build frontend for production

```bash
cd frontend
npm run build
```

The built files go to `frontend/dist/` and are served automatically by FastAPI — no separate frontend server needed.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a query → run all 6 agents → return response + agent outputs |
| `POST` | `/api/analyze` | Full analysis pipeline, returns complete JSON |
| `POST` | `/api/ingest` | Upload CSV, PDF, TXT, or MD files |
| `GET` | `/api/dashboard` | Aggregated KPIs and chart data |
| `GET` | `/api/report?format=pdf\|json` | Download last analysis as PDF or JSON |
| `GET` | `/api/health` | Service health + LLM provider status |

---

## Sample Data

The included `sample_data/Sample_Sales_Data.csv` contains:

- **120 rows** — daily sales transactions
- **10 products**: SmartWatch X, FitBand Pro, NoiseBuds Air, PowerBank Max, Gaming Mouse Pro, Wireless Keyboard, Smart Speaker, Security Camera, Tablet Lite, Laptop Air
- **5 categories**: Electronics, Wearables, Accessories, Audio, Smart Home
- **5 regions**: North, South, East, West, Central
- **Date range**: January – April 2026
- **Fields**: Revenue, Cost, Profit, Marketing Spend, Customer Rating, Returns, New Customers, Review text

---

## Docker (Optional)

```bash
cp .env.example .env
# Add your API keys to .env
docker-compose up --build
```

- Backend: http://localhost:8001
- Frontend: http://localhost:5173

---

## Features

- **Interactive Chat** — Ask questions in natural language; get AI-generated insights with SWOT grids, RICE tables, and opportunity scores
- **Live Dashboard** — Revenue trend, category breakdown, region radar, top products table — all from real data
- **PDF Reports** — Download a professional A4 strategy report with all agent outputs
- **Hybrid Search** — Combines dense vector search (ChromaDB) with BM25 keyword search, fused via Reciprocal Rank Fusion
- **LLM Failover** — Automatic 3-tier fallback: gpt-4o-mini → gpt-3.5-turbo → Groq llama-3.3-70b
- **Dark Mode** — Toggle via the navbar
