# MetaSignal Architecture

## Architecture Style

Batch-authoritative, production-simulated experimentation intelligence platform.

## Non-Goals

- Not a production SaaS system
- Not a frontend-first dashboard
- Not a real-time decisioning engine
- Not claiming real production traffic or real users

## Layers

### Event substrate

**Purpose:** Provides a real high-volume event base instead of toy CSV data.

**Components:**
- RetailRocket standardized parquet
- event_date/user_id/event_type normalization

### Storage and audit

**Purpose:** Stores metric definitions, results, pipeline runs, experiments, evaluations, decisions, and quality checks.

**Components:**
- Postgres
- SQLAlchemy models
- Alembic migrations

### Metric governance

**Purpose:** Prevents teams from using incompatible definitions of the same business metric.

**Components:**
- Metric registry
- denominator types
- metric conflict detector

### Data quality

**Purpose:** Blocks compute when data quality is not trustworthy.

**Components:**
- required-column checks
- row-count checks
- null checks
- domain checks
- failure injection

### Experiment evaluation

**Purpose:** Validates assignment quality and reduces variance before experiment decisions.

**Components:**
- deterministic assignment
- SRM check
- CUPED
- A/A validation

### Decisioning

**Purpose:** Turns metric evidence into auditable ship/hold decisions.

**Components:**
- guardrail-first decision engine
- decision log
- human review fields

### Reliability and validation

**Purpose:** Shows operational maturity beyond a one-off notebook analysis.

**Components:**
- right-censoring
- post-launch validation
- anomaly detection
- golden scenarios

### Serving

**Purpose:** Exposes the system as a platform, not just terminal scripts.

**Components:**
- FastAPI
- smoke-tested endpoints
- evidence/validation retrieval
