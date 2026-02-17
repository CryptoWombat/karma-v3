# Product Requirements Document (PRD)

# Karma Platform — Complete Rebuild & Validator API

**Version:** 1.0  
**Last Updated:** February 16, 2025  
**Status:** Draft  
**Owner:** Product / Engineering

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-02-16 | — | Initial PRD: rebuild spec + Validator API |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Success Criteria](#3-goals--success-criteria)
4. [Scope](#4-scope)
5. [User Personas](#5-user-personas)
6. [Functional Requirements](#6-functional-requirements)
7. [Validator API (New)](#7-validator-api-new)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [Technical Architecture](#9-technical-architecture)
10. [Data Model](#10-data-model)
11. [API Specification](#11-api-specification)
12. [Security Requirements](#12-security-requirements)
13. [Migration & Rollout](#13-migration--rollout)
14. [Out of Scope](#14-out-of-scope)
15. [Appendix](#15-appendix)

---

## 1. Executive Summary

This PRD defines the complete rebuild of the **Karma Platform** — a token economy backend powering a Telegram Mini App. The rebuild addresses critical reliability, security, and scalability issues in the current implementation. It also introduces a **Validator API** that allows externally managed validators to access authenticated, read-only platform data (user counts, balances, transaction metrics, inflation data, and leaderboards) for publishing, verification, or integration purposes.

---

## 2. Problem Statement

### Current State

The existing Karma API v1 has significant limitations:

- **Data persistence**: All state stored in flat JSON files; no ACID guarantees, high risk of corruption
- **Security gaps**: Unauthenticated endpoints (e.g. `/download`, `/unregister`) expose or allow destructive actions
- **Scalability**: Single-process, file-based design does not scale beyond small user bases
- **Protocol state**: Deferred rewards and maturity tracking reset on restart due to lack of persistence
- **Observability**: No structured logging, metrics, or monitoring
- **Validator integration**: No dedicated API for external validators to access platform data

### Desired State

A production-grade, database-backed platform with:

- ACID transactions, auditability, and data integrity
- Proper authentication and authorization on all endpoints
- Scalable architecture supporting 10,000+ users
- A dedicated **Validator API** for external validators to consume platform metrics and publish them

---

## 3. Goals & Success Criteria

### Goals

| Goal | Description |
|------|--------------|
| **G1** | Replace JSON file storage with a relational database (PostgreSQL) |
| **G2** | Implement proper authentication (Telegram + JWT) and admin authorization |
| **G3** | Preserve existing protocol behavior (emission, splits, deferred rewards, staking) |
| **G4** | Introduce a Validator API for external validators to access platform data |
| **G5** | Migrate existing users and balances without loss or inconsistency |
| **G6** | Establish testing, monitoring, and operational runbooks |

### Success Criteria

| ID | Criterion | Measurement |
|----|-----------|-------------|
| SC1 | Zero data loss during migration | Balance and history reconciliation |
| SC2 | All sensitive endpoints require authentication | Security audit / penetration test |
| SC3 | API p95 latency < 200ms for read endpoints | Monitoring |
| SC4 | Validator API serves required metrics within SLA | Uptime and correctness checks |
| SC5 | Protocol emission runs correctly with persisted state | Unit and integration tests |

---

## 4. Scope

### In Scope

- Complete backend rebuild (API, database, protocol engine)
- All existing user-facing features (register, send, stake, unstake, referral, swap)
- Admin capabilities (mint, unregister, stats, restore)
- **Validator API** for external validators
- Migration tooling and validation scripts
- Documentation for API and deployment

### Out of Scope (see §14)

- Telegram Mini App frontend changes (unless required for new auth flow)
- Blockchain integration (Karma remains off-chain)
- Mobile or web clients (beyond Telegram)
- Multi-currency beyond Karma and Chiliz

---

## 5. User Personas

| Persona | Description | Primary Needs |
|---------|-------------|---------------|
| **End User** | Telegram user interacting with Karma app | Register, send, stake, view balance, referrals |
| **Admin** | Platform operator | Mint, manage users, view stats, run protocol, restore |
| **Validator** | External entity operating a validator node | Access metrics via API to publish / verify platform data |
| **Developer** | Integrating or maintaining the platform | Clear API docs, test environment, observability |

---

## 6. Functional Requirements

### 6.1 User Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-UM-1 | Users register via Telegram; registration is idempotent | P0 |
| FR-UM-2 | Users can unregister themselves (data deletion / anonymization) | P0 |
| FR-UM-3 | Admins can force-unregister users | P0 |
| FR-UM-4 | User profile includes: telegram_user_id, username, created_at | P0 |
| FR-UM-5 | System and event wallets exist as special user types | P1 |

### 6.2 Wallets & Balances

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-WB-1 | Each user has a wallet with karma_balance and chiliz_balance | P0 |
| FR-WB-2 | Balances are non-negative; enforced at application layer | P0 |
| FR-WB-3 | Staked amount and rewards_earned tracked separately | P0 |
| FR-WB-4 | Balance endpoint returns balance, staked, rewards, chiliz | P0 |
| FR-WB-5 | Minimum send amount: 0.001 Karma | P0 |

### 6.3 Transfers

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-TX-1 | Users can send Karma to other registered users | P0 |
| FR-TX-2 | Optional note (max 30 chars) on send | P1 |
| FR-TX-3 | Insufficient balance returns clear error | P0 |
| FR-TX-4 | All transfers recorded in immutable transaction log | P0 |
| FR-TX-5 | Transaction history paginated (limit, offset, sort) | P0 |

### 6.4 Staking

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-ST-1 | Users stake Karma from liquid balance | P0 |
| FR-ST-2 | Users unstake to liquid balance (no lock period in v1) | P0 |
| FR-ST-3 | Stakers earn pro-rata rewards from protocol stakers bucket | P0 |
| FR-ST-4 | Stake info endpoint returns total_staked, available_to_unstake, liquid_karma | P0 |

### 6.5 Referrals

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-RF-1 | Inviter receives 1 Karma when invitee registers via referral | P0 |
| FR-RF-2 | Inviter receives 3 Karma on first send from invitee to inviter | P0 |
| FR-RF-3 | One invitee can only be referred once | P0 |
| FR-RF-4 | Referral status endpoint returns invited_by and rewarded | P0 |

### 6.6 Token Swap

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-SW-1 | Users can swap Karma ↔ Chiliz 1:1 | P0 |
| FR-SW-2 | Swap recorded in transaction history | P0 |

### 6.7 Protocol Emission

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-PE-1 | Block-based emission runs on configurable interval (e.g. 10 min) | P0 |
| FR-PE-2 | R = min(max(S/K, min_reward), max_reward); S = usage score | P0 |
| FR-PE-3 | UsageScore = sum(amounts) × √tx_count per receiver | P0 |
| FR-PE-4 | Splits: Stakers 10%, DevCo 15%, Validators 5%, Foundation 10%, Eligible 60% | P0 |
| FR-PE-5 | Stakers bucket distributed pro-rata to real stakers | P0 |
| FR-PE-6 | Deferred rewards when R_raw > max_reward; settled when capacity available | P0 |
| FR-PE-7 | Protocol state (deferred, utilization) persisted across restarts | P0 |
| FR-PE-8 | Admin can trigger emission manually via API | P0 |

### 6.8 Admin

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AD-1 | Admin can mint Karma to any user | P0 |
| FR-AD-2 | Admin can unregister users | P0 |
| FR-AD-3 | Admin can list users (paginated) | P0 |
| FR-AD-4 | Admin can view full network stats | P0 |
| FR-AD-5 | Admin can restore from backup | P0 |
| FR-AD-6 | Admin can create event wallets | P0 |
| FR-AD-7 | Admin can run protocol emission once | P0 |
| FR-AD-8 | No unauthenticated download of raw data | P0 |

### 6.9 Stats (Public)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-ST-1 | Public /stats returns: users, transactions, minted, transferred, total_in_circulation, available, savings, rewards_earned, last_block_*, foundation_balance | P0 |
| FR-ST-2 | No authentication required for public stats | P0 |

---

## 7. Validator API (New)

### 7.1 Overview

The **Validator API** is a dedicated, authenticated API surface for externally managed validators. Validators use it to fetch platform metrics and publish them (e.g. to blockchains, dashboards, or verification services). Access is restricted to entities with valid validator credentials.

### 7.2 Validator Persona

- **Who**: External validator operators (e.g. node operators, indexers, oracles)
- **Purpose**: Consume platform data to publish, verify, or integrate with other systems
- **Access**: Authenticated via validator API key or JWT; read-only
- **SLA expectation**: High availability, low latency for metrics endpoints

### 7.3 Validator Authentication

| ID | Requirement | Priority |
|----|-------------|----------|
| VA-AUTH-1 | Validators authenticate via `Authorization: Bearer <VALIDATOR_API_KEY>` | P0 |
| VA-AUTH-2 | Validator API keys are distinct from admin tokens | P0 |
| VA-AUTH-3 | API keys are issued per validator; revocable | P0 |
| VA-AUTH-4 | Rate limits may be higher than public API (e.g. 300 req/min) | P0 |
| VA-AUTH-5 | Failed auth returns 401 with no sensitive details | P0 |

### 7.4 Validator Data Requirements

Validators must be able to retrieve the following data via the API:

#### 7.4.1 User & Wallet Counts

| Field | Description | Example |
|-------|-------------|---------|
| `user_count` | Total number of registered user accounts | 1,234 |
| `wallet_count` | Total number of wallets with non-zero balance or history | 1,100 |
| `active_wallets_24h` | Wallets with at least one transaction in past 24h | 450 |

#### 7.4.2 Aggregate Balances

| Field | Description | Example |
|-------|-------------|---------|
| `total_karma_balance` | Sum of all karma_balance across wallets | 500,000.00 |
| `total_chiliz_balance` | Sum of all chiliz_balance across wallets | 10,000.00 |
| `total_staked` | Sum of all staked amounts | 200,000.00 |
| `total_rewards_earned` | Sum of rewards_earned for all users | 50,000.00 |

#### 7.4.3 Transaction Metrics (Amount & Volume)

| Metric | Windows | Description |
|--------|---------|-------------|
| `transaction_count` | 24h, 7d, 30d | Number of send + receive transactions |
| `transaction_volume_karma` | 24h, 7d, 30d | Sum of Karma transferred (send events) |
| `transaction_volume_chiliz` | 24h, 7d, 30d | Sum of Chiliz transferred (if applicable) |

#### 7.4.4 Inflation Data (Karma Minted)

| Metric | Windows | Description |
|--------|---------|-------------|
| `karma_minted` | 1h, 24h, 7d, 30d | Total Karma minted in the period (mint + protocol emission + stake rewards) |

**Clarification**: For protocol emission and stake rewards, "minted" means newly created Karma credited to wallets (not transferred from elsewhere). Breakdown may include:
- `mint_admin` – Admin mints
- `protocol_emission` – Protocol block rewards to system buckets + eligible pool
- `stake_rewards` – Rewards distributed to stakers from stakers bucket
- `referral_rewards` – Referral bonuses (1 + 3 Karma)

#### 7.4.5 Leaderboards (Top Wallets)

| Metric | Variations | Description |
|--------|------------|-------------|
| `top_wallets` | Top 10, 50, 100 | Sorted by combined karma_balance + staked, descending |
| Per-wallet fields | user_id, username, karma_balance, staked, total (balance + staked), rank | — |

### 7.5 Validator API Endpoints

#### Endpoint: `GET /v1/validator/snapshot`

Returns a comprehensive snapshot of all validator-required data in a single response. Optimized for validators that poll periodically.

**Auth**: Validator API key required.

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `include_top` | 10 \| 50 \| 100 | 10 | Number of top wallets to include |
| `timestamp` | ISO8601 | now | Reference time for window calculations (optional) |

**Response Schema**:

```json
{
  "snapshot_at": "2025-02-16T12:00:00Z",
  "windows": {
    "1h": { "start": "2025-02-16T11:00:00Z", "end": "2025-02-16T12:00:00Z" },
    "24h": { "start": "2025-02-15T12:00:00Z", "end": "2025-02-16T12:00:00Z" },
    "7d":  { "start": "2025-02-09T12:00:00Z", "end": "2025-02-16T12:00:00Z" },
    "30d": { "start": "2025-01-17T12:00:00Z", "end": "2025-02-16T12:00:00Z" }
  },
  "users": {
    "user_count": 1234,
    "wallet_count": 1100,
    "active_wallets_24h": 450
  },
  "balances": {
    "total_karma_balance": 500000.00,
    "total_chiliz_balance": 10000.00,
    "total_staked": 200000.00,
    "total_rewards_earned": 50000.00
  },
  "transactions": {
    "24h": { "count": 1200, "volume_karma": 15000.00, "volume_chiliz": 0 },
    "7d":  { "count": 8500, "volume_karma": 95000.00, "volume_chiliz": 200 },
    "30d": { "count": 35000, "volume_karma": 420000.00, "volume_chiliz": 1500 }
  },
  "inflation": {
    "1h":  {
      "karma_minted": 125.50,
      "breakdown": { "protocol_emission": 100.0, "stake_rewards": 20.0, "referral_rewards": 5.5, "mint_admin": 0 }
    },
    "24h": {
      "karma_minted": 2800.00,
      "breakdown": { "protocol_emission": 2400.0, "stake_rewards": 350.0, "referral_rewards": 45.0, "mint_admin": 5.0 }
    },
    "7d":  {
      "karma_minted": 19600.00,
      "breakdown": { "protocol_emission": 16800.0, "stake_rewards": 2450.0, "referral_rewards": 340.0, "mint_admin": 10.0 }
    },
    "30d": {
      "karma_minted": 84000.00,
      "breakdown": { "protocol_emission": 72000.0, "stake_rewards": 10500.0, "referral_rewards": 1400.0, "mint_admin": 100.0 }
    }
  },
  "top_wallets": [
    {
      "rank": 1,
      "user_id": "490851443",
      "username": "alice",
      "karma_balance": 15000.00,
      "staked": 8000.00,
      "total": 23000.00
    }
  ]
}
```

#### Endpoint: `GET /v1/validator/inflation`

Focused endpoint for inflation-only data. Lighter payload for validators that only need minting metrics.

**Auth**: Validator API key required.

**Query Parameters**: `timestamp` (optional)

**Response**: Same `inflation` and `windows` structure as in snapshot.

#### Endpoint: `GET /v1/validator/leaderboard`

Focused endpoint for top wallets only.

**Auth**: Validator API key required.

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | 10 \| 50 \| 100 | 10 | Number of top wallets |
| `sort_by` | balance \| total | total | Sort by liquid balance only or total (balance + staked) |

**Response**:

```json
{
  "generated_at": "2025-02-16T12:00:00Z",
  "top_wallets": [ /* same structure as snapshot */ ]
}
```

#### Endpoint: `GET /v1/validator/transactions`

Transaction metrics only.

**Auth**: Validator API key required.

**Response**: Same `transactions` and `windows` structure as in snapshot.

#### Endpoint: `GET /v1/validator/health`

Lightweight health check for validator integrations. Returns platform status without heavy queries.

**Auth**: Optional (validator key may get slightly more detail, e.g. last emission time).

**Response**:

```json
{
  "status": "operational",
  "database": "ok",
  "last_protocol_block_at": "2025-02-16T11:50:00Z",
  "timestamp": "2025-02-16T12:00:00Z"
}
```

### 7.6 Validator Data Freshness & Caching

| ID | Requirement | Priority |
|----|-------------|----------|
| VA-DATA-1 | Snapshot reflects data as of `snapshot_at`; windows are UTC-aligned | P0 |
| VA-DATA-2 | Inflation 1h/24h/7d/30d computed from transaction history (types: mint, protocol_emission, stake_reward, referral_* ) | P0 |
| VA-DATA-3 | Top wallets exclude system wallets by default; optional `include_system` flag | P1 |
| VA-DATA-4 | Caching allowed for snapshot (e.g. 60s TTL) to reduce DB load | P1 |
| VA-DATA-5 | Validator endpoints are read-only; no mutations | P0 |

### 7.7 Validator Admin Operations

| ID | Requirement | Priority |
|----|-------------|----------|
| VA-ADM-1 | Admin can create validator API keys (with optional name/label) | P0 |
| VA-ADM-2 | Admin can list and revoke validator keys | P0 |
| VA-ADM-3 | Revoked keys return 401 immediately | P0 |
| VA-ADM-4 | Key creation returns secret once; not retrievable later | P0 |

### 7.8 Validator Error Handling

| Code | Condition | Response |
|------|-----------|----------|
| 401 | Missing or invalid API key | `{"error": "unauthorized", "code": "INVALID_VALIDATOR_KEY"}` |
| 403 | API key revoked | `{"error": "forbidden", "code": "VALIDATOR_KEY_REVOKED"}` |
| 429 | Rate limit exceeded | `{"error": "rate_limit_exceeded", "retry_after": 60}` |
| 500 | Internal error | `{"error": "internal_error", "request_id": "..."}` |

---

## 8. Non-Functional Requirements

### 8.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-P1 | Public stats endpoint latency (p95) | < 200ms |
| NFR-P2 | Balance lookup latency (p95) | < 100ms |
| NFR-P3 | Validator snapshot latency (p95) | < 2s (cached) / < 5s (uncached) |
| NFR-P4 | Send transaction latency (p95) | < 300ms |
| NFR-P5 | Protocol emission block duration | < 30s for typical load |

### 8.2 Availability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-A1 | API uptime | 99.5% (excluding planned maintenance) |
| NFR-A2 | Database availability | 99.9% |
| NFR-A3 | Graceful degradation when Redis unavailable | Rate limiting disabled; auth may fall back |

### 8.3 Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-S1 | Concurrent users | 1,000+ |
| NFR-S2 | Transaction throughput | 100 tx/min sustained |
| NFR-S3 | User base | 10,000+ registered users |
| NFR-S4 | Transaction history | 1M+ events without significant degradation |

### 8.4 Observability

| ID | Requirement |
|----|-------------|
| NFR-O1 | Structured JSON logging (request_id, level, message) |
| NFR-O2 | Health endpoint (`/health`) for DB and Redis |
| NFR-O3 | Metrics: request count, latency, error rate by endpoint |
| NFR-O4 | Alerts on DB/Redis down, error spike, emission failure |
| NFR-O5 | Audit log for admin actions (mint, unregister, key management) |

---

## 9. Technical Architecture

### 9.1 Stack

| Component | Technology |
|-----------|------------|
| API framework | FastAPI |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Cache / sessions | Redis |
| Auth | JWT, Telegram initData verification |
| Background jobs | ARQ or Celery (Redis) |
| Deployment | Railway / Render / Fly.io |
| Testing | pytest, httpx, factory_boy |

### 9.2 Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│  Clients: Telegram Mini App │ Web (future) │ Validator Clients   │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Edge: Rate limiting, CORS, request validation                    │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  API Layer (FastAPI)                                               │
│  /v1/users | /v1/wallets | /v1/stake | /v1/admin | /v1/validator  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ PostgreSQL  │  │ Redis        │  │ Job Worker   │
│ (primary)   │  │ (cache,      │  │ (emission)   │
│             │  │  rate limit) │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## 10. Data Model

### 10.1 Core Tables

- **users**: id, telegram_user_id, username, created_at, updated_at, is_system_wallet, is_event_wallet
- **wallets**: id, user_id, karma_balance, chiliz_balance, staked_amount, rewards_earned, next_unlock_ts, updated_at
- **transactions**: id, created_at, type, actor_user_id, from_user_id, to_user_id, amount_karma, amount_chiliz, metadata, block_id
- **referrals**: id, invitee_user_id, inviter_user_id, rewarded, created_at
- **protocol_state**: id, last_processed_ts, last_emitted_block_id, deferred_state, utilization_window, saturated_days, updated_at
- **validator_api_keys**: id, key_hash, name, created_at, revoked_at
- **protocol_blocks**: id, block_id, emitted_at, reward_total, splits_applied, processed_tx_count

### 10.2 Transaction Types (Enum)

`mint`, `send`, `receive`, `stake_deposit`, `unstake_withdraw`, `stake_reward`, `referral_invite`, `referral_bonus`, `protocol_emission`, `stakers_distributed`, `swap`, `event_wallet_created`

### 10.3 Inflation Calculation

Inflation = sum of `amount_karma` for transactions where:
- `type IN ('mint', 'protocol_emission', 'stake_reward', 'referral_invite', 'referral_bonus')`
- `created_at` within the requested time window
- Excluding `from_user_id` = system wallets (credits to system buckets that are later distributed count when distributed)

**Refined rule**: Count as minted when Karma is **created** (not transferred). Thus:
- `mint` → always
- `protocol_emission` → always (new supply to system + eligible)
- `stake_reward` → always (new supply from stakers bucket to user)
- `referral_invite`, `referral_bonus` → always
- `send`, `receive` → never (transfers)
- `stakers_distributed` → not double-counted; stake_reward already counted when user received it

---

## 11. API Specification

### 11.1 Base URL & Versioning

- Base: `https://api.karma.example.com` (TBD)
- Version prefix: `/v1/`
- Content-Type: `application/json`

### 11.2 Auth Headers

| Context | Header | Example |
|---------|--------|---------|
| User (Telegram) | `Authorization: Bearer <JWT>` | After `/auth/telegram` |
| Admin | `Authorization: Bearer <ADMIN_API_KEY>` | Admin endpoints |
| Validator | `Authorization: Bearer <VALIDATOR_API_KEY>` | Validator endpoints |

### 11.3 Endpoint Summary

| Group | Endpoints |
|-------|-----------|
| Auth | POST /v1/auth/telegram |
| Users | POST /v1/users/register, POST /v1/users/unregister, GET /v1/users/me |
| Wallets | GET /v1/wallets/{id}/balance, POST /v1/wallets/send |
| Transactions | GET /v1/transactions |
| Stake | POST /v1/stake, POST /v1/unstake, GET /v1/stake/info |
| Referrals | POST /v1/referrals, GET /v1/referrals/status |
| Swap | POST /v1/swap |
| Stats | GET /v1/stats (public) |
| Admin | POST /v1/admin/mint, POST /v1/admin/unregister, GET /v1/admin/users, GET /v1/admin/stats, POST /v1/admin/protocol/run-once, POST /v1/admin/restore, POST /v1/admin/validator-keys |
| Validator | GET /v1/validator/snapshot, GET /v1/validator/inflation, GET /v1/validator/leaderboard, GET /v1/validator/transactions, GET /v1/validator/health |

---

## 12. Security Requirements

| ID | Requirement |
|----|-------------|
| SEC-1 | All admin endpoints require valid admin token |
| SEC-2 | All validator endpoints require valid validator API key |
| SEC-3 | User endpoints require valid JWT (issued after Telegram validation) |
| SEC-4 | Telegram initData verified with HMAC-SHA256 using bot token |
| SEC-5 | Validator and admin keys hashed (e.g. SHA-256); plaintext never stored |
| SEC-6 | Rate limiting: 60/min user, 300/min validator, 100/min admin (configurable) |
| SEC-7 | Input validation via Pydantic; max lengths, bounds on amounts |
| SEC-8 | No raw data export without authentication |
| SEC-9 | CORS restricted to known origins (Telegram, future web app) |
| SEC-10 | Secrets in environment only; never in code or logs |

---

## 13. Migration & Rollout

### 13.1 Migration Steps

1. Export legacy data (users, balances, history, referrals)
2. Transform and load into new schema
3. Reconciliation: compare balances and totals
4. Optional parallel run (dual-write to old and new)
5. Cutover: switch Telegram app to new API
6. Monitoring and rollback readiness

### 13.2 Phased Rollout

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1 | 2 weeks | DB, auth, register, balance, send |
| Phase 2 | 1 week | Stake, referral, swap, admin, public stats |
| Phase 3 | 1 week | Protocol engine, emission job, protocol state persistence |
| Phase 4 | 1 week | Validator API, admin key management |
| Phase 5 | 1 week | Migration scripts, hardening, monitoring |
| Phase 6 | 1 week | Cutover, validation, documentation |

---

## 14. Out of Scope

- Telegram Mini App UI changes (unless auth flow requires it)
- Blockchain or smart contract integration
- Native mobile or standalone web apps
- Additional tokens beyond Karma and Chiliz
- Real-time push (WebSocket) in v1
- Multi-region deployment in v1
- Formal legal/compliance (KYC, AML) — document for future consideration

---

## 15. Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| Karma | Primary platform token |
| Chiliz | Secondary token; 1:1 swap with Karma |
| Protocol emission | Block-based reward distribution from usage score |
| Deferred rewards | Owed rewards when block cap exceeded; settled later |
| Validator | External entity consuming Validator API data |
| Usage score | sum(amounts) × √tx_count per receiver |

### B. Validator API Key Lifecycle

1. Admin creates key via `POST /v1/admin/validator-keys` with optional name
2. Response includes `api_key` (plaintext) — shown once
3. Validator stores key securely; uses in `Authorization` header
4. Admin can revoke via `DELETE /v1/admin/validator-keys/{id}`
5. Revoked keys return 401 immediately

### C. Inflation Breakdown Details

- **protocol_emission**: Credits to protocol buckets (stakers, devco, validators, foundation, eligible) + distributions to eligible pool recipients
- **stake_rewards**: Credits from stakers bucket to user wallets
- **referral_invite**: 1 Karma to inviter on signup
- **referral_bonus**: 3 Karma to inviter on first send from invitee
- **mint_admin**: Admin mints

### D. References

- Original Karma API analysis (internal)
- Rebuild plan v1 (internal)
- Telegram WebApp initData verification: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

---

*End of PRD*
