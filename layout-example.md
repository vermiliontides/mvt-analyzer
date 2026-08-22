verichron-epoch/
├── .venv/                          # Dedicated Python virtual environment (git-ignored)
├── requirements.txt                # Pinned Python dependencies (ileapp, psycopg, etc.)
├── contracts/                      # Shared data schemas and type contracts
│   ├── EXTRACTOR_CONTRACT.md
│   ├── normalized_record.py
│   ├── normalized-record.schema.json
│   └── normalizedRecord.ts
├── db/                             # Database management & migration runner
│   ├── migrate.py
│   └── migrations/
│       └── 0001_init.sql
├── extractors/                     # Modular Python ingestion & extraction pipeline
│   ├── db_writer.py                # Shared database insertion utility
│   ├── crash/
│   │   ├── main.py
│   │   └── README.md
│   ├── mvt_iocs/                   # MVT analytical verdict processor & IOC trigger
│   │   ├── main.py
│   │   └── README.md
│   ├── ileapp_bridge/              # Python translation layer for iLEAPP outputs
│   │   ├── main.py
│   │   └── README.md
│   ├── network/
│   │   └── README.md
│   ├── safari/
│   │   └── README.md
│   └── sms/
│       └── README.md
├── core/                           # Shared Python orchestration, correlation, and analysis logic
│   ├── correlate.py                # Temporal correlation engine (±15 min window logic)
│   ├── reporting/
│   │   └── generate_report.py      # Markdown/HTML correlation report generator
│   └── analysis/
│       ├── automated_forensics.py
│       └── forensics_benchmark.py
├── orchestrators/                  # TypeScript Node processes & execution runners
│   ├── mvt-runner/
│   │   ├── main.ts
│   │   ├── package.json
│   │   ├── package-lock.json
│   │   └── tsconfig.json
│   └── main-orchestrator/          # Controls stage execution and Python process spawning
│       ├── main.ts
│       ├── package.json
│       ├── package-lock.json
│       └── tsconfig.json
├── docs/                           # Project reference docs & architecture blueprints
│   ├── architecture.md
│   ├── Backend Architecture.docx
│   ├── Integrations.docx
│   ├── Marketing Strategy.docx
│   ├── Product Vision.docx
│   └── UI Spec.docx
├── infra/                          # Local environment configs
│   └── docker-compose.yml
├── correlation_report.md           # Sample output artifact
├── README.md
└── RUNBOOK.md