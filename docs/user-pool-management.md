# PostgreSQL User Pool Management Schema

This document contains the SQL queries to create tables for user-pool management using PostgreSQL.

## Prerequisites

First, enable the UUID extension:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

## Table Definitions

### Users Table

The main users table stores core user information:

```sql
CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  email varchar(255) NOT NULL UNIQUE,
  email_verified boolean NOT NULL DEFAULT false,
  full_name varchar(255),
  password_hash varchar(255),            -- nullable for OAuth-only accounts
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  metadata jsonb DEFAULT '{}'            -- extra fields
);
```

### OAuth Accounts Table

Stores OAuth provider information (Google, future providers):

```sql
CREATE TABLE oauth_accounts (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider varchar(64) NOT NULL,         -- e.g. 'google'
  provider_user_id varchar(255) NOT NULL,-- e.g. Google's "sub"
  provider_email varchar(255),
  extra jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (provider, provider_user_id)
);
```

### OTP Codes Table

Manages OTP codes for email verification and password reset:

```sql
CREATE TABLE otp_codes (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  email varchar(255) NOT NULL,
  otp_hash varchar(128) NOT NULL,        -- store hash(otp + salt)
  salt varchar(64) NOT NULL,
  purpose varchar(32) NOT NULL,          -- 'email_verification' | 'password_reset'
  expires_at timestamptz NOT NULL,
  consumed boolean NOT NULL DEFAULT false,
  attempts integer NOT NULL DEFAULT 0,
  ip_addr varchar(64),
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Index for efficient email lookups
CREATE INDEX idx_otp_email ON otp_codes (email);
```

### Refresh Tokens Table

Stores refresh tokens (opaque tokens stored hashed):

```sql
CREATE TABLE refresh_tokens (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash varchar(128) NOT NULL,
  user_agent varchar(512),
  ip_addr varchar(64),
  expires_at timestamptz NOT NULL,
  revoked boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  replaced_by uuid NULL
);

-- Index for efficient user lookups
CREATE INDEX idx_refresh_user ON refresh_tokens (user_id);
```

### Auth Events Table

Optional table for sessions and audit events:

```sql
CREATE TABLE auth_events (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid,
  event_type varchar(64) NOT NULL, -- 'login', 'logout', 'otp_requested',...
  payload jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
```

## Key Features

- **UUID Primary Keys**: All tables use UUID primary keys for better security and scalability
- **Timestamptz**: Uses timezone-aware timestamps for proper time handling
- **JSONB Fields**: Flexible metadata and extra data storage using JSONB
- **Foreign Key Constraints**: Proper referential integrity with CASCADE deletes
- **Indexes**: Performance optimization for frequently queried fields
- **OAuth Support**: Ready for multiple OAuth providers
- **Security**: Password hashes and OTP hashes with salt for secure storage
- **Audit Trail**: Auth events table for tracking user activities

## Usage Notes

- The `password_hash` field is nullable to support OAuth-only accounts
- OTP codes include rate limiting through the `attempts` field
- Refresh tokens can be chained using the `replaced_by` field
- All sensitive data (passwords, OTPs) should be properly hashed before storage
- The `metadata` JSONB field allows for flexible user profile extensions