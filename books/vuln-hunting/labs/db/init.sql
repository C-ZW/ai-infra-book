CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    owner_email TEXT NOT NULL,
    balance_cents BIGINT NOT NULL DEFAULT 10000,
    withdraw_limit_cents BIGINT NOT NULL DEFAULT 10000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    id BIGSERIAL PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    delta_cents BIGINT NOT NULL,
    idempotency_key TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO tenants (id, name) VALUES
    ('tenant-alpha', 'Alpha Merchant'),
    ('tenant-beta', 'Beta Merchant')
ON CONFLICT (id) DO NOTHING;

INSERT INTO accounts (id, tenant_id, owner_email, balance_cents, withdraw_limit_cents) VALUES
    ('acct-alpha-01', 'tenant-alpha', 'alice@alpha.local', 10000, 10000),
    ('acct-beta-01',  'tenant-beta',  'bob@beta.local',    10000, 10000)
ON CONFLICT (id) DO NOTHING;
