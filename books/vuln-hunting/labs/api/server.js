import http from "node:http";
import pg from "pg";
import { createClient } from "redis";

const PORT = Number(process.env.PORT || 3000);
const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
const redis = createClient({ url: process.env.REDIS_URL });
redis.on("error", (err) => console.error("[redis]", err.message));
await redis.connect();

const json = (res, status, body) => {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": Buffer.byteLength(payload),
  });
  res.end(payload);
};

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);

  if (req.method === "GET" && url.pathname === "/health") {
    const dbRes = await pool.query("SELECT 1 AS ok");
    const pong = await redis.ping();
    return json(res, 200, {
      service: "nexuspay-api",
      db: dbRes.rows[0]?.ok === 1,
      redis: pong === "PONG",
      keepAliveTimeoutMs: server.keepAliveTimeout,
    });
  }

  if (req.method === "GET" && url.pathname === "/v1/accounts") {
    const { rows } = await pool.query(
      "SELECT id, tenant_id, owner_email, balance_cents, withdraw_limit_cents FROM accounts ORDER BY id"
    );
    return json(res, 200, { accounts: rows });
  }

  return json(res, 404, { error: "not_found", path: url.pathname });
});

// Matches NexusPay baseline: Node.js keepAliveTimeout = 5 s
server.keepAliveTimeout = 5000;
server.listen(PORT, "0.0.0.0", () => {
  console.log(`[nexuspay-api] listening on :${PORT} (keepAliveTimeout=${server.keepAliveTimeout}ms)`);
});
