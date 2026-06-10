# ch04 — 語言與工具橋接：Python、PyTorch、Go、CUDA

> **本章解決什麼問題**：前三章建立了 GPU 與推論的心智模型，但 AI infra 的日常工作是用你還不熟的語言進行的：serving 與 glue code 是 Python、K8s 控制面是 Go、kernel 層是 CUDA/C++。這章用你的 TypeScript/Node.js 經驗當錨點，把四個生態各自壓到「夠用的深度」——Python 要能寫生產服務、PyTorch 要能讀懂 vLLM 在寫什麼、Go 要能讀懂 controller 並做小修改、CUDA 生態要能認名詞與讀 stack trace。後面所有章節的程式碼與工具都建立在這章之上。

## 從你已知的出發

你已經會一件比語法更難學的事：在生產環境寫出不會半夜叫醒你的服務。語言只是載體。先把 AI infra 的語言地圖攤開：

```
產品 API / glue / serving 邏輯      Python   （FastAPI、vLLM 的上層、各種 router）
K8s 控制面 / operator / 排程器      Go       （device plugin、Kueue、llm-d 的 EPP）
推論引擎核心 / kernel               C++ / CUDA / Triton（vLLM 的底層、FlashAttention）
前端與部分 CLI 工具                 TypeScript（你的主場，但在這個領域是配角）
```

關鍵是**每個語言要求的深度不同**。把目標說清楚，可以省掉你三個月的瞎學：

| 語言 | 目標深度 | 對應的日常任務 |
|---|---|---|
| Python | **能寫**生產級服務 | 寫 proxy/router/webhook、改 vLLM 設定、寫 benchmark 腳本 |
| PyTorch | **能讀** | 讀懂 vLLM/SGLang 原始碼的 forward path、看懂 issue 裡的程式碼片段 |
| Go | **能讀＋小改** | 讀懂 controller 的 reconcile 邏輯、改一個 scoring 函式、提小 PR |
| CUDA 生態 | **能認得** | 讀 stack trace、查版本相容矩陣、知道該把問題丟給誰 |

你的遷移優勢比想像中大。Node 的單執行緒 event loop 直覺幾乎原封不動地對應到 asyncio；NestJS 的 decorator、DI、validation pipe 對應到 FastAPI 的 decorator、`Depends`、pydantic；你寫過的 SQS idempotent consumer——desired state 對 actual state 的對帳邏輯——就是 K8s controller 的 reconcile loop，只是換了語言。這章的寫法是「對照優先」：每個新概念都先告訴你它等於你已知的什麼，再講差異在哪、坑在哪。

## Python：給 TypeScript 工程師的最短遷移路徑

### 工具鏈對照表

2026 年學 Python 比五年前幸福非常多，因為工具鏈經歷了一場「Rust 化」整併——你會發現新一代工具的使用體驗刻意向 npm/cargo 看齊。直接用新的，不要碰教學文章裡的舊路徑（pip + virtualenv + requirements.txt + setup.py 那一套你只需要看得懂，不需要用）。

| 你熟的（TS/Node） | Python（2026 年的選擇） | 備註 |
|---|---|---|
| node 直譯器 / nvm | CPython / `uv python install 3.12` | uv 連直譯器版本都幫你管，nvm 的角色它一起做了 |
| npm / pnpm | **uv** | Astral 出品，Rust 寫的，比 pip 快一到兩個數量級；2026-03 OpenAI 宣布收購 Astral（交易尚待監管批准），維護承諾不變（2026-06） |
| package.json | pyproject.toml | 結構幾乎同構：metadata + dependencies + tool config |
| package-lock.json | uv.lock | 一樣要進版控 |
| node_modules/ | .venv/ | 概念不同：不是套件目錄，是一個隔離的直譯器環境；`uv run` 會自動幫你進對的環境 |
| npx | uvx | 臨時跑一個 CLI 工具不污染環境 |
| tsc + tsconfig.json | mypy 或 pyright | 靜態型別檢查器，**只在 CI/編輯器跑，runtime 不存在**；Astral 的 ty still in beta，目標 2026 年出 1.0（2026-06） |
| eslint + prettier | **ruff** | 一個工具同時做 lint + format，也是 Astral/Rust 系 |
| jest / vitest | pytest | fixture 機制比 jest 的 setup/teardown 強大，值得花一小時學 |
| Express | Flask（上一代）/ FastAPI | 看到 Flask 教學可以直接跳過 |
| NestJS（DI、decorator、pipes） | **FastAPI** | decorator 路由、`Depends` 依賴注入、pydantic 當 validation pipe，心智模型高度重疊 |
| class-validator + class-transformer / zod | **pydantic** | 宣告式 schema + runtime 驗證 + 序列化，v2 核心是 Rust 寫的 |
| fetch / axios / undici | **httpx**（async）/ requests（sync，舊生態） | httpx 同時支援 sync/async，API 模仿 requests |
| Promise / async-await | coroutine / asyncio | 語法神似，語義有陷阱，下面細講 |
| EventEmitter / Readable stream | async generator（`async def` + `yield`） | SSE streaming 的標準寫法 |

起手式只有三行：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # 裝 uv
uv init my-service && cd my-service               # 等同 npm init
uv add fastapi httpx "uvicorn[standard]"          # 等同 npm install
```

### 三個必踩的坑

#### 坑一：GIL——以及 2026 年的 free-threading 現況

GIL（Global Interpreter Lock）是 CPython 的一把全域鎖：**一個 process 內，同一時刻只有一條 thread 能執行 Python bytecode**。對你來說這個心智模型其實很親切——你在 Node 早就活在單執行緒世界。差別是：Node 根本不給你 thread（worker_threads 是隔離的）；Python 給你 thread，但 CPU 並行被 GIL 鎖死，thread 只對「等待 I/O」有用。

那為什麼整個 AI 產業跑在 Python 上沒被 GIL 掐死？因為**重活都不在 Python 裡**。PyTorch 的矩陣乘法進到 C++/CUDA 後會釋放 GIL；tokenizer 是 Rust 寫的；Python 只負責指揮。這就是 Python 在 ML 的真實角色：一個人體工學極好的 C++/CUDA 指揮層。需要真正 CPU 並行時，生態的標準答案是 multiprocess——vLLM 的引擎架構就是多個 process 各司其職（見 ch08），跟你用 Node cluster mode 繞過單執行緒是同一個思路。

現況（2026-06）：Python 3.14（目前 3.14.5）依 PEP 779 把 free-threading（no-GIL）從 experimental 升級為 officially supported，單執行緒效能損耗從 3.13 的約 40% 降到約 5–10%。但注意三件事：GIL 預設仍然開啟；free-threaded 是一個**獨立的 build**（`python3.14t`），不是開關；大量 C extension（包括部分 ML 生態）的相容性還在過渡期。我的建議：2026 年的生產服務繼續用預設 build + multiprocess，把 free-threading 當成「面試能講清楚現況」的知識點，而不是架構依賴。

#### 坑二：async 生態的分裂

TS 的 async 生態是統一的：所有東西都回傳 Promise。Python 的不是。你會遇到三條斷層線：

1. **sync/async 函式庫二分**。`requests` 是 sync、`httpx` 是 async（也支援 sync）；很多舊函式庫只有 sync 版。在 async 函式裡呼叫 sync 的阻塞 I/O，會凍結整條 event loop——你在 Node 用 `fs.readFileSync` 踩過的坑，這裡以更隱蔽的方式重現，因為 Python 的 sync 函式長得跟 async 的一模一樣，沒有編譯器擋你。
2. **event loop 實作分裂**：asyncio（標準庫）之外還有 trio/anyio。你只需要知道 asyncio 是主流、FastAPI 底層用 anyio 抽象，看到 trio 風格的 API（structured concurrency）知道它在講什麼即可。
3. **FastAPI 的 `def` vs `async def` 陷阱**：`async def` handler 跑在 event loop 上，`def` handler 會被丟進 threadpool（預設 40 條 thread）。所以「在 `async def` 裡呼叫 `requests`」會卡死所有人，但「在 `def` 裡呼叫 `requests`」反而沒事——這個行為對 Node 工程師是反直覺的，記下來。

把 Python 的併發選項整理成決策框架，工作來了照表抓：

| 工作性質 | 用什麼 | 理由與代價 |
|---|---|---|
| 網路 I/O 密集（proxy、router、webhook） | asyncio + async 函式庫 | 跟你的 Node 直覺一致；代價是整條呼叫鏈都得是 async，混入一個 sync 呼叫就全毀 |
| 偶發的 blocking 呼叫（舊函式庫、檔案 I/O） | `asyncio.to_thread()` 丟 threadpool | GIL 在等 I/O 時會釋放，threadpool 對 I/O 有效；對 CPU-bound 無效 |
| CPU-bound（大量 tokenize、壓縮、解析） | multiprocess（`ProcessPoolExecutor`）或交給 Rust/C++ 函式庫 | 繞過 GIL 的正道；代價是跨 process 序列化開銷與記憶體翻倍 |
| GPU-bound | 不關 Python 的事 | 重活在 CUDA kernel 裡，Python 只負責別擋路（別在熱路徑插 blocking 呼叫） |

#### 坑三：型別只是註記

TS 的型別至少有編譯期強制——`tsc` 不過就是不過。Python 的 type hints 在執行期**完全不存在**：`def f(x: int)` 傳進字串照樣跑，跑到爆炸為止。防線有兩道，缺一不可：

- **CI 防線**：mypy 或 pyright 當作你的 `tsc --noEmit`，沒過不准合。
- **邊界防線**：pydantic 在所有資料進入點（HTTP body、設定檔、佇列訊息）做 runtime 驗證——角色完全等同你在 NestJS 用 class-validator 守 DTO、或用 zod 守 API 邊界。內部函式之間靠 type hints + CI，邊界靠 pydantic，這是 2026 年 Python 服務的標準分工。

### Worked example：同一個併發 HTTP 呼叫，TS vs Python 逐行對照

需求：併發呼叫多個 URL，每個呼叫帶 2 秒逾時、最多重試 3 次（指數退避）、5xx 與網路錯誤可重試、4xx 直接失敗、聚合所有結果不要 fail-fast。這是你寫過一百遍的程式，現在看它在兩個語言的長相。

你熟的 TS 版（Node 24 LTS，2026-06）：

```typescript
// fetch_all.ts
class HttpError extends Error {
  constructor(public status: number, msg: string) { super(msg); }
}

const retryable = (e: unknown) =>
  e instanceof HttpError ? e.status >= 500 : true;     // 網路錯誤/timeout 一律可重試

async function fetchWithRetry(url: string, retries = 3, timeoutMs = 2_000) {
  let lastErr: unknown;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) }); // (1)
      if (!res.ok) throw new HttpError(res.status, `upstream ${res.status}`);
      return await res.json();                                                  // (2)
    } catch (err) {
      lastErr = err;
      if (!retryable(err) || attempt === retries) throw err;
      await new Promise((r) => setTimeout(r, 2 ** attempt * 100));              // (3)
    }
  }
  throw lastErr;
}

const urls = ["http://localhost:11434/api/tags" /* , ... */];
const results = await Promise.allSettled(urls.map((u) => fetchWithRetry(u)));   // (4)(5)
for (const r of results)
  console.log(r.status === "fulfilled" ? r.value : `FAILED: ${r.reason}`);
```

語義相同的 Python 版（3.12+）：

```python
# fetch_all.py — uv add httpx 之後 uv run fetch_all.py
import asyncio
import httpx

def retryable(err: Exception) -> bool:
    if isinstance(err, httpx.HTTPStatusError):
        return err.response.status_code >= 500
    return isinstance(err, (httpx.TransportError, TimeoutError))

async def fetch_with_retry(client: httpx.AsyncClient, url: str,
                           retries: int = 3, timeout_s: float = 2.0):
    for attempt in range(retries + 1):
        try:
            async with asyncio.timeout(timeout_s):                    # (1)
                res = await client.get(url)
            res.raise_for_status()        # 4xx/5xx 變成 exception
            return res.json()             # (2) 注意：沒有 await——httpx 的 .json() 是同步的
        except Exception as err:
            if not retryable(err) or attempt == retries:
                raise
            await asyncio.sleep(2 ** attempt * 0.1)                   # (3)

async def main():
    urls = ["http://localhost:11434/api/tags"]  # 換成你的目標
    async with httpx.AsyncClient() as client:                         # (6)
        coros = (fetch_with_retry(client, u) for u in urls)           # (7) 此刻什麼都還沒發生！
        results = await asyncio.gather(*coros, return_exceptions=True)  # (4)(5)
    for url, r in zip(urls, results):
        print(url, "->", f"FAILED: {r!r}" if isinstance(r, BaseException) else r)

asyncio.run(main())                                                   # (8)
```

逐點對照（編號對應兩段程式碼的註解）：

| # | TS | Python | 差異與坑 |
|---|---|---|---|
| (1) | `AbortSignal.timeout()` | `asyncio.timeout()` | JS 的取消是**合作式 API**（被呼叫方要支援 signal）；Python 的取消是**語言級機制**——timeout 到期會把 `CancelledError` 注入 coroutine 的 await 點，任何 await 中的操作都會被打斷。更強，但也意味著你的 cleanup 邏輯（`finally`）必須能在任意 await 點被觸發 |
| (2) | `await res.json()` | `res.json()` | fetch 的 body 是 stream 所以 `.json()` 回 Promise；httpx 非 streaming 模式下 body 已讀完，`.json()` 是同步的。對它 `await` 不會錯（Python 會直接報錯），但**該 await 沒 await 才是大坑**，見 (7) |
| (3) | `new Promise(r => setTimeout(r, ms))` | `asyncio.sleep(s)` | Python 原生提供，且**單位是秒不是毫秒**——這個單位差異在 timeout 設定上錯一次就是 2000 秒的逾時 |
| (4) | `Promise.allSettled` | `gather(return_exceptions=True)` | 語義等價。但 `gather` **預設**是類似 `Promise.all` 的 fail-fast——而且第一個錯誤拋出後，其餘 task 仍在背景繼續跑、結果沒人收，是殭屍工作的常見來源。3.11+ 的 `asyncio.TaskGroup` 才有「一人失敗、取消全組」的 structured concurrency 語義 |
| (5) | callback 風格 map | generator 解包 | 寫法差異而已 |
| (6) | fetch 內建全域連線池 | `AsyncClient` 要自己管生命週期 | **每個請求 new 一個 client = 沒有 keep-alive、每次重建 TLS**，是 Python 服務最常見的效能 bug 之一。建一次、全程共用、結束時關閉 |
| (7) | async 函式**呼叫即執行**（eager） | coroutine 是 **lazy** | `fetch_with_retry(...)` 呼叫當下什麼都不會發生，要等 `await` 或包成 task。忘記 await 的症狀：一行 `RuntimeWarning: coroutine ... was never awaited` 警告，然後你的邏輯**靜默地沒有執行**。這是 TS 工程師寫 Python 的第一大坑 |
| (8) | top-level await | `asyncio.run()` | Python 沒有 top-level await（REPL 除外），進入點要顯式起 event loop |

把這張表讀熟，你的 TS async 直覺就能安全著陸。

## 你會寫一輩子的 glue code：FastAPI streaming proxy

AI infra 工程師寫得最多的服務形態，就是「站在 OpenAI-compatible API 前面或後面的東西」：加認證、加計量、加路由、加快取、改寫請求。它們的共同骨架是一個會轉發 SSE streaming 的 proxy。這裡給一個完整可跑的版本，後面章節的 gateway、admission control、token 計量（見 ch12、ch16）都會在這個骨架上長出來。

SSE（Server-Sent Events）對你不是新東西——它就是單向的、跑在純 HTTP 上的 WebSocket 替代品：`Content-Type: text/event-stream`，每個事件是 `data: {...}\n\n`，以空行分隔。OpenAI-compatible API 的 streaming 回應就是一連串 `data:` 事件，最後一個是 `data: [DONE]`。你做過 WebSocket + Redis Pub/Sub 的訊息 fan-out，所以這些工程問題你都處理過：長連線的生命週期、斷線時的資源清理、中間層 buffering。差別在於 LLM 的 SSE 連線**每一秒都在燒 GPU**——一條沒清乾淨的殭屍連線，在遊戲後端是洩漏一個 socket，在這裡是白燒一張卡的算力，所以下面範例對清理路徑的偏執是有價格依據的。

```toml
# pyproject.toml
[project]
name = "llm-proxy"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.136",        # 2026-06 時點的當前系列
    "uvicorn[standard]>=0.30",
    "httpx>=0.28",
    "pydantic>=2.13",
]
```

```python
# main.py — OpenAI-compatible streaming proxy
# 跑法：uv run uvicorn main:app --port 8000
import json
import logging
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

UPSTREAM_BASE = "http://localhost:11434/v1"   # Ollama 的 OpenAI-compatible endpoint
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("proxy")


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="allow")   # 多模態 content、tool_calls… 原樣放行
    role: str
    content: str | list | None = None


class ChatCompletionRequest(BaseModel):
    # proxy 的驗證哲學：只驗自己要用的欄位，其餘全部放行。
    # pydantic 預設 extra="ignore" 會「默默丟掉」不認識的欄位——
    # 對一個 proxy 來說，這等於上游每加一個新參數你就吃掉一個，是資料遺失 bug。
    model_config = ConfigDict(extra="allow")
    model: str
    messages: list[ChatMessage] = Field(min_length=1)
    stream: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 全服務共用一個 AsyncClient：連線池 + keep-alive（對照上一節的坑 (6)）
    app.state.client = httpx.AsyncClient(
        base_url=UPSTREAM_BASE,
        timeout=httpx.Timeout(connect=5.0, write=10.0, pool=5.0, read=300.0),
        # read=300s 不是拍腦袋：streaming 的 read timeout 管的是「兩個 chunk 之間」
        # 的最大間隔。一般 ITL 遠小於 1s，但 reasoning 模型可能長時間停頓，
        # 這個值要照你上游的 ITL p99.9 設（見 ch14）。
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    yield
    await app.state.client.aclose()


app = FastAPI(lifespan=lifespan)


def error_json(status: int, message: str) -> JSONResponse:
    # 維持 OpenAI 錯誤格式，下游 SDK 才解析得了
    return JSONResponse(
        {"error": {"message": message, "type": "proxy_error"}}, status_code=status
    )


@app.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest, request: Request):
    client: httpx.AsyncClient = request.app.state.client
    payload = body.model_dump(exclude_none=True)   # extra="allow" 的欄位也會一起 dump

    if not body.stream:  # ---- 非串流：單純的請求轉發 ----
        try:
            res = await client.post("/chat/completions", json=payload)
        except httpx.TimeoutException:
            return error_json(504, "upstream timeout")
        except httpx.TransportError as exc:
            return error_json(502, f"upstream unreachable: {exc}")
        return JSONResponse(res.json(), status_code=res.status_code)

    # ---- 串流：async generator 轉發 SSE ----
    async def relay():
        start = time.perf_counter()
        ttft_logged = False
        try:
            async with client.stream("POST", "/chat/completions", json=payload) as up:
                if up.status_code != 200:
                    # 我們已對下游送出 200 + SSE header，HTTP 狀態碼追不回來了，
                    # 只能用 SSE event 回報錯誤——這是 streaming 協定的固有限制。
                    detail = (await up.aread()).decode(errors="replace")
                    yield f'data: {json.dumps({"error": {"message": detail}})}\n\n'
                    return
                async for line in up.aiter_lines():
                    if not ttft_logged and line.startswith("data:"):
                        log.info("TTFT %.0f ms", (time.perf_counter() - start) * 1e3)
                        ttft_logged = True
                    yield line + "\n"   # aiter_lines 連空行都會吐，補回 \n 即還原 SSE 框架
        except httpx.TimeoutException:
            yield 'data: {"error": {"message": "upstream stalled (read timeout)"}}\n\n'
        finally:
            # 下游斷線時，Starlette 會對這個 generator 注入取消；
            # async with 保證上游連線一定被關閉——不關，上游就會繼續白算 token（token 是錢）。
            log.info("stream closed after %.1f s", time.perf_counter() - start)

    return StreamingResponse(
        relay(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        # X-Accel-Buffering: no → 告訴 nginx 類反向代理不要 buffer，
        # 否則你的 streaming 會被攢成一大包再吐出來，TTFT 直接報廢。
    )


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
```

驗證（先 `ollama pull` 一個小模型，把 `model` 換成你 `ollama list` 裡有的名字）：

```bash
uv run uvicorn main:app --port 8000
curl -N http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model": "llama3.2", "stream": true,
       "messages": [{"role": "user", "content": "用一句話解釋 KV cache"}]}'
```

`-N` 關掉 curl 的 buffering，你應該看到 `data:` 事件逐塊吐出，proxy log 印出 TTFT。這 100 行包含了生產 proxy 的所有要素雛形：共用連線池、分層 timeout、串流中錯誤的協定限制、下游斷線時的上游清理、反向代理 buffering 的對抗。每一條都對應一種真實事故（見本章故障模式一節）。

## PyTorch：讀碼能力，不是訓練能力

你不需要會訓練模型。你需要的是打開 vLLM 的 model 程式碼時，能看懂它在算什麼——因為你排查效能問題時，stack trace 的盡頭就是這些 forward 函式。

### tensor 的四個屬性

tensor 是 PyTorch 的唯一主角：一塊帶 metadata 的多維數值陣列，類比「有 shape 資訊的 TypedArray」。讀碼時你只需要追蹤它的四個屬性：

- **shape**：維度大小，如 `[batch, seq_len, hidden]`。**讀 PyTorch 碼 = 追蹤 shape 的變化**，這是唯一主線。好的程式碼會用註解標 shape，vLLM 裡大量這種註解。
- **dtype**：每個元素的數值格式（fp32/bf16/fp8…），直接決定記憶體用量與能用哪種 tensor core（ch02）。
- **device**：`cpu`、`cuda:0`、Apple Silicon 上是 `mps`。`.to(device)` 是顯式的資料搬運——每次搬運都走 PCIe 或統一記憶體，是錢也是延遲（ch02）。看到 forward path 裡有 `.cpu()` 或 `.item()`，那是 GPU→CPU 的同步點，效能 bug 的常見藏身處。
- **requires_grad**：是否記錄梯度。推論永遠不需要，所以推論碼一定包在 `torch.no_grad()` 或更激進的 `torch.inference_mode()` 裡——省掉 autograd 的簿記與中間結果的保留，少吃一大塊記憶體。看到它就知道「這是推論路徑」。

### 30 行 attention：把 ch03 變成可執行的程式碼

ch03 講過 attention 的數學與 prefill/decode 的分野。以下 30 行在 M1 上可直接跑（`uv add torch`），每行對應 ch03 的一個概念。為了行數這裡是單一 head 群、且直接拿輸入當 Q/K/V（真實模型有 `W_q/W_k/W_v` 三個投影矩陣、GQA 的 KV heads 少於 Q heads——ch03），屬可運行的簡化版：

```python
# attention.py — ch03 的注意力機制，30 行 PyTorch
import torch
import torch.nn.functional as F

B, H, D = 1, 8, 64        # batch、heads、head_dim（ch03：d_model = H × D）
torch.manual_seed(0)

def attention(q, k, v):
    # q: [B, H, T_q, D]；k, v: [B, H, T_kv, D]
    scores = q @ k.transpose(-2, -1) / D**0.5         # QK^T → [B, H, T_q, T_kv]，O(n²) 的來源
    T_q, T_kv = scores.shape[-2], scores.shape[-1]
    mask = torch.tril(torch.ones(T_q, T_kv, dtype=torch.bool), diagonal=T_kv - T_q)
    scores = scores.masked_fill(~mask, float("-inf")) # causal mask：只能看過去
    return F.softmax(scores, dim=-1) @ v              # 注意力加權和 → [B, H, T_q, D]

@torch.inference_mode()                               # 推論：關掉 autograd 簿記
def run():
    # --- prefill：整段 prompt（16 個 token）一次算，矩陣大 → compute-bound（ch03）---
    x = torch.randn(B, H, 16, D)
    k_cache, v_cache = x.clone(), x.clone()           # KV cache 誕生：[B, H, 16, D]
    out = attention(x, k_cache, v_cache)

    # --- decode：每步只進 1 個新 token ---
    for step in range(4):
        x_new = torch.randn(B, H, 1, D)               # T_q = 1
        k_cache = torch.cat([k_cache, x_new], dim=2)  # KV 線性成長：ch03 公式的「× tokens」
        v_cache = torch.cat([v_cache, x_new], dim=2)
        out = attention(x_new, k_cache, v_cache)      # 1 個 query 掃整個 cache → memory-bound
        print(f"step {step}: q={tuple(x_new.shape)} kv={tuple(k_cache.shape)} out={tuple(out.shape)}")

run()
```

跑起來你會看到 decode 階段 `q` 永遠是 `[1, 8, 1, 64]`、`kv` 從 17 長到 20。這四行輸出就是 ch03 全部論證的可執行版本：decode 的計算量小（T_q=1）但每一步都要讀完整個 KV cache 與全部權重——arithmetic intensity 低，memory-bound（ch02 roofline）。另外注意 `torch.cat` 每步都在重新配置一塊更大的連續記憶體——這正是 naive KV 管理的浪費所在，PagedAttention 解的就是這個問題（見 ch05）。

### 讀 vLLM 原始碼的實戰守則

- **只追 shape**。看到 `view`、`reshape`、`transpose`、`einsum`，那是 shape 整形，不是數學；真正的計算只有矩陣乘與少數幾個算子。
- **找 `forward`**。PyTorch 的 module 慣例：`__init__` 宣告權重、`forward` 是執行路徑。推論引擎裡你只關心 forward。
- **跳過訓練碼**。看到 `loss`、`backward`、`optimizer` 直接略過，推論用不到。
- **`@` 就是 matmul**。`a @ b` 是矩陣乘法運算子，跟你在 ch02 算 roofline 的 GEMM 是同一個東西。

## Profiling Python：把你的方法論搬過來

你靠 profiling 把 RDS CPU 尖峰降了 40%——先量測、找到真正的熱點、修正、再用數據證明。那套方法論（全書主軸之一）在 Python 一個字都不用改，換的只是工具。你用 Clinic.js/0x 做過的事——對線上服務取樣、看 flame graph、找熱點——在 Python 的對應物是 **py-spy**（2026-04 的 v0.4.2 支援到 CPython 3.14）。它是 Rust 寫的 sampling profiler，從 process 外部讀取目標的記憶體來重建 call stack，**不需改碼、不需重啟、overhead 極低**，production-safe：

```bash
uv tool install py-spy
py-spy top --pid <PID>                  # 即時熱點，像 top
py-spy record -o profile.svg --pid <PID> --duration 30   # 30 秒 flame graph
py-spy dump --pid <PID>                 # 印出當下所有 thread 的 call stack
```

`py-spy dump` 值得特別記住：它是 Python 版的 `kill -3` thread dump。當你的 FastAPI 服務「活著但不回應」（event loop 被某個 blocking call 卡住），一發 dump 直接看到卡在哪一行——這是排查 async 服務假死的第一工具。

`cProfile` 是標準庫的 deterministic profiler（逐呼叫記錄），overhead 大、會扭曲時間分布，適合離線跑腳本，不適合對線上服務。分工跟你熟的一樣：取樣式看生產、精確式看開發。

邊界要認清：py-spy 只看得到 Python 層的 stack。一旦時間花在 torch 的 C++/CUDA kernel 裡，py-spy 只會顯示卡在某個 Python 呼叫上，看不進去。GPU 側的 profiling 是另一套工具（torch profiler、Nsight Systems，見 ch07）。判斷準則：py-spy 負責回答「Python glue 層慢不慢」，GPU profiler 負責「kernel 慢不慢」。

## Go：讀懂 K8s controller 的最短路徑

### 為什麼 infra 控制面是 Go 的天下

K8s 本身是 Go 寫的，整個 operator/controller 生態（client-go、controller-runtime）跟著是 Go；AI infra 的控制面元件——NVIDIA 的 device plugin 與 DRA driver、Kueue、llm-d 的 inference scheduler——清一色是 Go。原因務實：編譯成單一靜態 binary（container image 小、無 runtime 依賴）、goroutine 讓高併發的 watch/reconcile 寫起來像同步碼、加上 K8s 生態的重力。你不需要會寫 Go 服務，但讀不懂 Go 等於 K8s 生態的原始碼對你全部上鎖（ch11 會大量遇到）。

### goroutine、channel 與你的 event loop 直覺

Node 的併發模型：單執行緒 event loop + 非同步 I/O，併發靠「不阻塞」。Go 反過來：**寫阻塞式的同步碼，讓 runtime 去排程**。goroutine 是極輕量的綠色執行緒（初始 stack 約 2KB，可開百萬個），Go runtime 把它們 M:N 地排到 OS thread 上。所以 Go 沒有 async/await、沒有函式顏色問題——`http.Get()` 就是阻塞呼叫，阻塞的只是這條 goroutine，不是整個程式。

channel 用你的語言講就是「行程內的型別化 SQS」：goroutine 之間不共享記憶體溝通，而是透過 channel 傳訊息；`select` 陳述式同時等多個 channel，等同你同時 poll 多條佇列。`ctx context.Context` 出現在每個函式的第一個參數，它是 Go 的取消與逾時傳播機制——角色等同 `AbortSignal`，但慣例上無處不在。

### 讀懂一個 reconcile loop

K8s controller 的核心是你已經寫過的東西。你的 SQS idempotent consumer 是怎麼運作的？訊息觸發處理，但處理函式**不信任訊息內容**，而是去查當前實際狀態、對照期望狀態、補齊差距；重複投遞無害，因為操作冪等。controller 的 reconcile loop 一模一樣：event（資源變更）只是觸發器，reconcile 函式拿到的只有資源的名字，它自己去讀 desired state（spec）與 actual state（叢集現況），然後收斂差距。這叫 **level-triggered**（看狀態）而非 edge-triggered（看事件）——跟你做最終一致性結算 pipeline 的設計理由完全相同：事件會丟、會重複、會亂序，狀態才可靠。

一個極簡 controller 的 reconcile（示意：節錄自 controller-runtime 風格的程式碼，省略 import 與註冊樣板）：

```go
// 假想 CRD：ModelServer，spec 裡宣告要跑的模型與副本數
func (r *ModelServerReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    // req 只有 namespace/name——沒有「發生了什麼事」。這就是 level-triggered：
    // 不管觸發原因是建立、修改還是 controller 重啟後的全量重放，處理邏輯都一樣。
    var ms servingv1.ModelServer
    if err := r.Get(ctx, req.NamespacedName, &ms); err != nil {
        // 物件已被刪掉：不是錯誤，是「期望狀態 = 不存在」，收工。
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    desired := r.desiredDeployment(&ms)            // 從 spec 推導期望的 Deployment

    var actual appsv1.Deployment
    err := r.Get(ctx, client.ObjectKeyFromObject(desired), &actual)
    if apierrors.IsNotFound(err) {
        // actual 不存在 → 建立。冪等：若兩次 reconcile 撞在一起，
        // 第二次 Create 會吃 AlreadyExists 錯誤、觸發 requeue，下一輪走更新路徑。
        return ctrl.Result{}, r.Create(ctx, desired)
    }
    if err != nil {
        return ctrl.Result{}, err                  // 回傳 error → 自動指數退避重排
        //（≈ SQS 的 visibility timeout 到期重新投遞 + backoff）
    }

    if *actual.Spec.Replicas != *desired.Spec.Replicas {
        actual.Spec.Replicas = desired.Spec.Replicas
        if err := r.Update(ctx, &actual); err != nil {
            return ctrl.Result{}, err              // 衝突（resourceVersion 過期）也走這裡：
        }                                          // 樂觀鎖失敗就重來，跟你處理 DB 衝突一樣
    }
    return ctrl.Result{RequeueAfter: 5 * time.Minute}, nil
    // 即使沒有 event 也定期再對帳——對抗 drift 的最後防線
}
```

讀懂這 30 行，ch11 的 device plugin、Kueue、llm-d EPP 的原始碼對你就只剩領域知識的問題，沒有語言問題。

### 讀 Go 的五條速成規則

1. **大寫開頭 = exported（public），小寫 = package 私有**。沒有 `public/private` 關鍵字。
2. **`if err != nil` 不是噪音，是控制流**。Go 沒有 exception，錯誤是回傳值；每個 `if err != nil` 都是一個顯式的失敗路徑——讀碼時這些分支就是你要的故障行為地圖。
3. **`defer` ≈ `finally`**，註冊在函式返回時執行，慣用於釋放鎖與關閉資源。
4. **struct embedding ≈ mixin**：struct 裡只寫型別不寫欄位名，等於把那個型別的方法「攤平」進來。K8s API 型別大量使用（`metav1.ObjectMeta` 無處不在）。
5. **指標只管「共享與否」**：`*T` 能改到原值、`T` 是複本；沒有指標運算，不用怕。

## CUDA 生態：名詞表與消歧義

先說結論：AI infra 工程師 95% 的時間**不寫** CUDA，但每天**讀**它——讀 stack trace、讀版本相容矩陣、讀「為什麼裝不起來」。這張表的目的是讓每個名詞在你腦中有正確的層級定位：

| 名詞 | 它是什麼 | 解什麼系統問題 | 你什麼時候碰到 |
|---|---|---|---|
| **CUDA**（driver + toolkit + runtime） | GPU 的「作業系統 + 編譯工具鏈」 | 讓一般程式能對 GPU 提交工作 | 天天。裝環境時的版本地獄：**kernel driver 與 CUDA toolkit 是兩個東西、各有版本**，driver 向後相容舊 toolkit，反之不行 |
| **nvcc / PTX / SASS** | CUDA 編譯器／中間表示／實際機器碼 | 同一份 kernel 跨 GPU 世代分發 | 看到 `no kernel image is available for execution on the device` ＝ 這個 wheel 沒帶你這張卡的架構編譯產物 |
| **cuBLAS / cuBLASLt** | NVIDIA 官方 GEMM（矩陣乘）庫 | 讓矩陣乘逼近硬體峰值（ch02 roofline 的「屋頂」） | LLM 推論的算力大頭。stack trace 裡的 `CUBLAS_STATUS_*` 錯誤 |
| **cuDNN** | NN 原語庫（卷積、normalization 等） | 深度學習常用算子的官方最佳化 | LLM 時代重要性下降（attention 另有專門 kernel），但 PyTorch 仍相依，裝錯版本照樣炸 |
| **CUTLASS** | C++ template 的 GEMM 建構庫 | 讓人組裝客製 GEMM（如 FP8/FP4 混精度） | 讀 vLLM 的量化 kernel 原始碼時（ch07） |
| **NCCL** | 多 GPU 集合通訊庫（all-reduce 等） | 多卡之間高效交換資料 | 多卡部署的一切（機制見 ch09；它 hang 起來的痛見 ch15） |
| **Triton（語言）** | OpenAI 開源的 Python DSL，寫 GPU kernel 不用碰 C++（2026-05 時點為 3.7 系列） | 把「寫高效 kernel」的門檻從 CUDA C++ 降到 Python | `torch.compile` 預設把計算圖 lower 成 Triton kernel；vLLM 大量 kernel 以 Triton 寫成。讀引擎原始碼必遇 |

**消歧義，這題面試會考**：**Triton 語言**（OpenAI 的 GPU kernel DSL，`triton-lang`）與 **NVIDIA Triton Inference Server**（NVIDIA 的通用模型 serving 伺服器）**完全無關，只是撞名**。前者是寫 kernel 的工具，活躍且是 PyTorch 編譯棧的預設後端；後者是前 LLM 時代的 serving 標準（TensorFlow/ONNX/TensorRT 模型的通用託管），在 LLM serving 場景 NVIDIA 已把主推位置交給 Dynamo（見 ch10/ch12）。看 JD 或文章時用上下文判斷：講 kernel、跟 PyTorch 並列的是語言；講 deployment、跟 serving 並列的是伺服器。

版本相容矩陣的現實，用一條鏈記住：**GPU 架構 ← driver ← CUDA toolkit ← PyTorch build ← vLLM release**。每一環都有最低版本要求，PyTorch 的 wheel 名稱裡的 `cu130` 就是「以 CUDA 13.0 編譯」（PyTorch 2.12，2026-05 時點的當前版，預設 CUDA 13.0）。環境炸掉時，先對這條鏈逐環比對，比讀任何錯誤訊息都快。

## 故障模式與防禦

本章的工具在生產環境怎麼壞、長什麼樣、怎麼防——這張表值得貼在桌前：

| 故障 | 症狀 | 怎麼觀測 | 防禦 |
|---|---|---|---|
| 在 `async def` 裡呼叫 blocking I/O（`requests`、`time.sleep`、大檔同步讀） | **所有** in-flight SSE stream 同時凍結，ITL 集體 spike，然後同時恢復——鋸齒狀延遲 | `py-spy dump` 看 event loop 所在 thread 卡在哪一行 | 只用 async 函式庫；真要跑 blocking 工作丟 `asyncio.to_thread()`；CI 加 lint 規則禁 import requests |
| 忘記 `await` coroutine | 邏輯靜默未執行；log 出現 `coroutine ... was never awaited` | 蒐集 RuntimeWarning 進日誌管線並告警 | pyright/mypy 會抓多數案例——這就是 CI 型別檢查不可省的理由 |
| 每請求新建 `httpx.AsyncClient` | 無 keep-alive、TLS 重建，p50 多幾十 ms，上游連線數爆炸 | 上游看到大量短命連線 | client 放 lifespan，全服務共用 |
| 上游 hang 而無 read timeout | 連線池被殭屍請求佔滿 → 池耗盡 → 新請求全部排隊，服務「活著但全 timeout」 | pool 等待時間飆升；`py-spy dump` 大量 stack 停在網路讀取 | 永遠顯式設四種 timeout（connect/read/write/pool）；streaming 的 read timeout 照 ITL p99.9 設 |
| pydantic `extra="ignore"`（預設）用在 proxy | 上游新增參數被默默吃掉，功能「壞得很安靜」 | 對比進出 payload 的欄位差 | proxy/gateway 一律 `extra="allow"`；嚴格 schema 留給自己擁有的 API |
| 反向代理 buffer SSE | 下游 TTFT 變成「整段生成時間」，streaming 名存實亡 | curl `-N` 直連 vs 過 proxy 對比 TTFT | `X-Accel-Buffering: no`、`Cache-Control: no-cache`，並驗證每一層代理設定 |
| 下游斷線未清理上游 stream | 上游照算整段回應——燒的是 GPU 時間與錢 | 上游完成數 > 下游完成數 | 靠 `async with` 確保取消傳播；對照本章 proxy 的 `finally` |
| CPU-bound 工作（超大 JSON、tokenize）佔住 event loop | 與 blocking I/O 同症狀，但 py-spy 顯示忙在計算而非等待 | `py-spy top` 熱點 | 搬進 process pool 或交給 Rust 系函式庫（GIL 一節的教訓） |
| reconcile 不冪等 | 資源重複建立、或 controller 重啟後狀態錯亂 | 監看 reconcile error rate 與資源數量異常 | 永遠「讀 actual → 比對 desired → 收斂」，禁止「假設上次做到哪」 |
| reconcile 無條件 requeue 0s | controller hot loop：CPU 滿載、API server 被打爆 | controller CPU 與 API server QPS | 回傳 error 讓框架做指數退避，不要自己 `RequeueAfter: 0` |
| CUDA 版本鏈斷裂 | `import torch` 直接炸；或更糟——**靜默 fallback 到 CPU，慢 50 倍但不報錯** | 啟動時主動 assert `torch.cuda.is_available()` 並打印 device，進 readiness probe | 鎖死 base image 的 driver/toolkit/torch 版本三元組，升級走 canary（ch15） |

注意一個共通模式：這個生態最危險的故障都是**靜默的**——coroutine 沒執行不報錯、欄位被吃掉不報錯、fallback 到 CPU 不報錯。防禦的核心是把「應該發生的事」變成顯式斷言與指標。

## 動手做

### Lab 4-1 [M1]：跑起 streaming proxy，並打出它的原形

1. 裝 Ollama，`ollama pull llama3.2`（或任何 3B 級小模型）。
2. 照本章程式碼建好 `llm-proxy` 專案，`uv run uvicorn main:app --port 8000`。
3. 用 `curl -N` 驗證 streaming 與 `[DONE]` 結尾；確認 proxy log 有 TTFT。
4. 用你熟的 k6 做併發測試。注意：k6 的 `http` 模組會 buffer 整個回應，**量不到 TTFT**，只能量 E2E——所以用 proxy 自己的 TTFT log 做延遲觀測，k6 負責製造併發（要在 k6 內量 SSE 需要社群 extension xk6-sse，狀態請自行查證）：

```javascript
// k6-stream.js — 製造併發，E2E 延遲 + 錯誤率
import http from "k6/http";
export const options = { vus: 20, duration: "60s" };
export default function () {
  const res = http.post("http://localhost:8000/v1/chat/completions",
    JSON.stringify({ model: "llama3.2", stream: true,
      messages: [{ role: "user", content: "count to 20" }] }),
    { headers: { "Content-Type": "application/json" }, timeout: "120s" });
  if (res.status !== 200) console.error(res.status, res.body.slice(0, 200));
}
```

5. **成功標準**：20 VU 下 proxy 零 5xx；從 log 整理出 TTFT 的 p50/p95；能解釋 TTFT 隨併發上升的原因（M1 上的 Ollama 一次只能算一個 batch——這正是 ch06 continuous batching 要解的問題）。

### Lab 4-2 [M1]：用 py-spy 抓出埋好的 bug

1. 在 proxy 的 `chat_completions` 開頭埋一行 `time.sleep(0.2)`（模擬有人寫了 blocking 呼叫）。
2. 重跑 k6，觀察吞吐崩跌、延遲鋸齒化。
3. `py-spy record -o profile.svg --pid <uvicorn 的 PID> --duration 30`，打開 SVG。
4. **成功標準**：在 flame graph 上指出 `time.sleep` 那條 frame 與它佔的時間比例；換成 `await asyncio.sleep(0.2)` 再測一次，解釋為什麼吞吐恢復了（event loop 不再被佔住），而單請求延遲仍多 200ms。

### Lab 4-3 [紙上推演]：讀一段真實的推論碼

打開 vLLM repo 裡任一個 model 實作（如 `vllm/model_executor/models/llama.py`），找到 attention 相關的 `forward`，對每個 tensor 寫下你推斷的 shape，與本章 30 行版本對照。**成功標準**：能指出 Q 與 KV 的 head 數在哪裡分岔（GQA，ch03），以及 KV cache 從哪個參數傳進來。

## 這個領域往哪走

短評三點。其一，free-threading 已是官方支援（2026-06），但 phase III（預設關 GIL）未到，C extension 生態的遷移以年計——推論引擎的 multiprocess 架構短期內不會因此改寫。其二，Python 工具鏈與效能關鍵路徑的「Rust 化」會繼續：uv/ruff/ty、pydantic-core、tokenizers 都是 Rust，連 vLLM 都出現實驗性 Rust frontend（2026-06 的 release notes，細節未驗證）；Python 越來越像「介面層語言」，這反而鞏固了它的地位。其三，語言分工（Python 介面、Go 控制面、CUDA/Triton kernel）在可見的未來是穩態——能在三者之間自由穿梭的工程師，正是 platform 與 inference 團隊之間最稀缺的接縫人才。這章教的「讀」的能力，貶值速度會比任何框架知識都慢。

## 自我檢核

1. GIL 鎖住的到底是什麼？為什麼 PyTorch 推論沒有被 GIL 卡死？2026 年 free-threading 的官方狀態是什麼、你會在生產服務用嗎，為什麼？
2. FastAPI 的 `async def` 與 `def` handler 執行模型差在哪？「在 `async def` 裡呼叫 `requests.get`」的症狀長什麼樣，怎麼用 py-spy 證明？
3. `asyncio.gather` 的預設行為與 `Promise.all`、`Promise.allSettled` 各差在哪？失敗時其餘 task 的命運是什麼？`TaskGroup` 改變了什麼？
4. 你的 SSE proxy 在上游已開始 streaming 後才發生錯誤，為什麼不能回 HTTP 502？正確做法是什麼？
5. 解釋 `q @ k.transpose(-2, -1)` 的輸出 shape，它對應 ch03 的什麼？為什麼 decode 階段 T_q 永遠是 1，這個事實如何證明 decode 是 memory-bound？
6. `torch.inference_mode()` 替推論省下了什麼？讀 vLLM forward 路徑時，看到 `.item()` 或 `.cpu()` 為什麼要警覺？
7. 為什麼 reconcile loop 必須冪等？level-triggered 與 edge-triggered 差在哪？對應到你寫過的 SQS consumer，「回傳 error 觸發 requeue」等於 SQS 的什麼機制？
8. Triton 語言與 NVIDIA Triton Inference Server 各是什麼？vLLM 跟其中哪一個有關係、什麼關係？

## 延伸閱讀

- [Python Free-Threading HOWTO（官方）](https://docs.python.org/3/howto/free-threading-python.html) — free-threading 的權威現況說明，面試講 GIL 前先讀這份。
- [uv 官方文件](https://docs.astral.sh/uv/) — 半小時讀完 project 管理那幾頁，你的 Python 工具鏈問題就解決了 90%。
- [FastAPI：Concurrency and async / await](https://fastapi.tiangolo.com/async/) — 官方把 `def` vs `async def` 的執行模型講得最清楚的一篇。
- [pydantic 官方文件](https://docs.pydantic.dev/latest/) — 重點讀 models 與 `model_config` 兩章，對照你的 class-validator 經驗。
- [HTTPX：Async Support](https://www.python-httpx.org/async/) — 連線池、timeout 與 streaming API 的一手資料，本章 proxy 的所有設定出處。
- [PyTorch 官方教學：Tensors](https://pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html) — 只需要讀 tensor 基礎這篇，訓練部分全部跳過。
- [py-spy（GitHub）](https://github.com/benfred/py-spy) — README 即完整文件，重點看 `record`/`dump` 與「為什麼 production-safe」一節。
- [A Tour of Go](https://go.dev/tour/) — 兩個晚上走完，達到本章要求的「能讀」門檻綽綽有餘。
- [The Kubebuilder Book](https://book.kubebuilder.io/) — 想把 reconcile loop 從「能讀」升級到「能寫」時的標準教材，讀完 Tutorial 即可。
- [Triton 語言官方文件](https://triton-lang.org/) — 不用會寫，讀 introduction 理解它在 kernel 生態的位置即可，ch07 會再遇到它。
