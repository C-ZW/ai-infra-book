# 外部事實與時效基準（Source Evidence — ch07-graphql-grpc-websocket）

本文件記錄《邊界失守》[第 7 章：非 REST 現代後端協定安全（GraphQL、gRPC 與 WebSocket）] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章涵蓋現代 API 協定解析面，包含 GraphQL 巢狀查詢深度限制、gRPC Protobuf 序列化邊界與 CSWSH 握手驗證。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **OWASP API Security Top 10:2023**：截至 2026 年底仍為最新正式版（API1 BOLA、API2 Broken Authentication、API3 BOPLA、API4 Unrestricted Resource Consumption、API5 BFLA、API6 Sensitive Business Flows、API7 SSRF、API8 Security Misconfiguration、API9 Improper Inventory Management、API10 Unsafe Consumption of APIs）。⚠️ 需留意 2027 年是否釋出新版。
  - 來源：OWASP API Security Project（https://owasp.org/API-Security/）

- **Web / API 實驗基準**：PortSwigger Web Security Academy（免費且涵蓋 HTTP Smuggling、Race Condition、OAuth 等現代議題）。
  - 來源：PortSwigger Research（https://portswigger.net/research）
