# ch12 — event loop 與單執行緒並發：一條執行緒怎麼扛上萬連線、又怎麼被一行字殺死

> **本章解決什麼問題**：ch05 給過你結論——「一行同步重運算能把整台 Node 機器拖死」。那一章只用了一條鐵律（event loop 單執行緒、不搶占）就把現象說完，把機制留了個白。這一章把那個白填滿：那條唯一的執行緒**底下到底怎麼轉**？它一圈圈走過哪幾個相位、各相位處理什麼、microtask 在哪些縫隙裡被清空、為什麼 `process.nextTick` 能餓死你的 I/O、為什麼你的 `fs.readFile` 走 thread pool 而你的 3,200 條 WebSocket 不走。這是 Part IV「橫切老問題」裡專屬「並發」這一軸的深潛——ch05 的卡頓是它的病例，這一章是它的解剖。worker_threads 的實作細節、V8 GC 的內部、把 event loop 當 processor-sharing 近似的排隊數學，都點到為止並指路（分別見後文、ch17 點到、《等待的數學》queue 書）。

## 從你已知的出發

你整個職涯的後端——NeoBards 那套扛 500K+ 使用者、10K+ CCU 的服務，LetsTalk 那套撐 ~3,200 並發連線、~10M 訊息/月的即時通知——全部站在同一顆東西上：Node 的 event loop。你寫的每一個 route handler、每一個 `await`、每一次 `socket.send`，都排隊在這一條執行緒上跑。

ch05 那次你已經摸到它的邊了。那次你用 profiling 抓出一個同步重運算，把它丟出 hot path，尾延遲掉下來。當時你接受了一條結論：「Node 單執行緒、不搶占，所以一個 callback 跑太久，後面全部乾等。」這條結論是對的，你也靠它解決了問題。但它是一句**口號**——你當時沒往下問，這條「唯一的執行緒」自己到底在做什麼。

我猜你腦中的 event loop 大概長這樣：「有一個迴圈，不停地撈事件、跑 callback，撈完跑、跑完撈。」這個圖**沒錯，但太糊**。它糊到無法回答這些你其實天天踩到的問題：

- 你寫過排程訊息（ch09），知道 `setTimeout` 不精確、「限 15 分鐘」是在跟不穩定性妥協。但你說得清楚 `setTimeout(fn, 100)` 為什麼**保證不會在 100ms 整準時觸發、只保證不早於 100ms**嗎？那個延遲是從哪個相位漏出來的？
- 你大概看過一段「混了 `setTimeout`、`Promise.then`、`setImmediate`、`process.nextTick` 的程式，輸出順序很反直覺」的面試題。你能不能不靠背、而是**從相位推**出它的順序？
- 你知道「不要在主執行緒做重活」。但你的 `fs.readFile` 其實**不在**主執行緒上讀檔——它在背景執行緒。那為什麼你的 3,200 條 WebSocket 的網路讀寫**反而在**主執行緒上？這條線你劃得出來嗎？
- `process.nextTick` 你大概當成「比 `setTimeout(fn, 0)` 更快的延後執行」在用。你知道它用過頭會**餓死整個 I/O 系統**——讓你的網路請求一個都進不來嗎？

這些不是冷知識。它們是「並發」這一軸（五軸裡的第四軸：兩件事同時發生會打架嗎、誰跟誰搶資源、怎麼排）在 Node 上的**具體長相**。你當年隱性地回答過它們——你的服務沒當機、連線扛得住，代表你大致沒踩雷。這一章把那些隱性答案攤開，讓你能口頭講出來：這顆 loop 是哪一種並發、強在哪、什麼工作會殺死它、為什麼。

先把全章最大的那個誤會清掉——「並發」跟「平行」不是同一件事。

## 並發 ≠ 平行：交錯不是同時

這是整章的地基，也是最多人嘴上會、心裡糊的一句。

- **平行（parallelism）**：兩件事**真的在同一個瞬間**各自進行。你需要兩個（以上）的執行單元——兩顆 CPU 核心、兩條 OS 執行緒各占一核。Java 的 thread-per-request 模型就是這個：1,000 個請求進來，理論上可以有 1,000 條執行緒，OS 排程器把它們攤到所有核心上，**真的同時**在算。
- **並發（concurrency）**：好幾件事「在進行中」（in progress），但**不一定在同一瞬間執行**。它們可以**交錯（interleave）**——A 跑一下、讓出、B 跑一下、讓出、A 再跑——在一條執行緒上輪流。從外面看，A 和 B 都「在處理中」；但放大到任一個瞬間，CPU 上只有一個在跑。

Node 的 event loop 是**並發、不是平行**。它在**一條執行緒**上，靠**快速地在成千上萬個「在進行中」的工作之間切換**，製造出「同時在服務上萬連線」的效果。但任何一個瞬間，CPU 上只有一個 callback 在跑。

這聽起來像個缺陷——「只有一條執行緒，那不是很弱？」關鍵在於：**後端服務的瓶頸，絕大多數時候不是 CPU，是等待**。等資料庫回來、等 Redis 回來、等對方 socket 把資料送完。一個請求的生命週期裡，真正「在算」的時間可能只有 1%，剩下 99% 都在**等 I/O**。

平行模型（thread-per-request）怎麼處理這個等待？它讓那條執行緒**卡在那裡等**（阻塞 I/O）。1,000 個請求大多在等，就有 1,000 條執行緒大多卡著——每條執行緒吃掉 MB 級的 stack 記憶體、OS 要為上千條執行緒做上下文切換（context switch，本身有成本）。連線數一上去，光是「掛著等」就把記憶體和排程器吃垮。

event loop 模型反過來：它**不為等待保留執行緒**。當一個請求要等資料庫，event loop 不卡著——它把「等」這件事登記出去（交給 OS 的 epoll），**立刻轉去服務別的請求**；等資料庫回來了，再回頭跑那個請求剩下的 callback。一條執行緒，靠「絕不停下來等」這個紀律，就能同時掛著上萬條**大多在等待**的連線。

```
┌────────────────────────────────────────────┐
│ 平行模型（thread-per-connection）          │
├────────────────────────────────────────────┤
│ 每條連線配一條 OS 執行緒、各占一核         │
│ 請求大多在「等 I/O」→ 執行緒大多卡著       │
│ 3,200 連線 ≈ 3,200 條執行緒的記憶體＋      │
│ OS 為它們做上下文切換 → 連線一多就垮       │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ 並發模型（event loop）                     │
├────────────────────────────────────────────┤
│ 單一執行緒，絕不停下來等                   │
│ c1 算→登記等→c2 算→登記等→c3 算…           │
│ → c1 的 I/O 好了 → 回頭跑 c1 剩下的        │
│ 在「等」的縫隙裡塞滿別人 → 一條扛 3,200    │
└────────────────────────────────────────────┘
```

> **我以為 vs 實際。** 你大概把「Node 適合高並發」記成「Node 很快」。不對。Node 的**單一請求**未必比多執行緒語言快——它甚至慢，因為所有 JS 擠在一條執行緒上。Node 強的是**在大量 I/O 密集連線下，用極少資源維持極多「在進行中」的工作**。它賣的不是「算得快」，是「**等得有效率**」——把別人浪費在「掛著等」的執行緒成本，全部省下來塞進同一條執行緒的等待縫隙裡。所以判準很清楚：**I/O 密集（等很多、算很少）→ event loop 是神；CPU 密集（算很多、等很少）→ event loop 是錯的工具**（為什麼錯，本章後半見分曉）。

這就帶出一個必然的代價，也是 ch05 那條鐵律的根：並發靠的是「**自願讓出**」。A 跑一下、**自己讓出**、B 才有機會。沒有人能強迫 A 讓出（不搶占）。所以只要有一個 callback **不讓出**——一行同步重運算、一個沒有 `await` 的大迴圈——這條唯一的執行緒就被它霸占，整個並發機制當場垮掉。要看懂「讓出」到底發生在哪些時機，就得打開這顆 loop，看它一圈圈怎麼轉。

## libuv 的相位：一圈圈轉的那顆心臟

Node 的 event loop 不是「一個籠統的迴圈」。它底下的 **libuv**（C 寫的跨平台非同步 I/O 函式庫）把每一圈（一次 tick）切成**固定順序的幾個相位（phase）**，每個相位有自己的一條 callback 佇列，**只處理屬於它那一類的 callback**。loop 一圈圈轉，每圈都按同一個順序走過這些相位。

順序是這樣（2026-06，以 libuv 官方 design 文件與 Node 官方 event loop 文件為準）：

```
        ┌─────────────────────────────────────────────────┐
        │                                                 │
        ▼                                                 │
 ┌──────────────┐  ① timers           到期的 setTimeout / setInterval 的 callback
 │   timers     │                     （到期＝現在時間 ≥ 設定的觸發時間）
 └──────┬───────┘
        ▼
 ┌──────────────┐  ② pending          上一圈被延後的某些系統層 I/O callback
 │   pending    │                     （如某些 TCP 錯誤）；你平常很少直接碰
 └──────┬───────┘
        ▼
 ┌──────────────┐  ③ idle / prepare   libuv 內部使用（你的程式碼幾乎碰不到）
 │ idle/prepare │
 └──────┬───────┘
        ▼
 ┌──────────────┐  ④ poll（I/O）      ★ 核心相位：在這裡「等」I/O，並跑
 │     poll     │                     已完成 I/O 的 callback（網路讀寫、檔案讀完…）
 └──────┬───────┘                     沒事做時，loop 就阻塞在這裡等新 I/O
        ▼
 ┌──────────────┐  ⑤ check            setImmediate 的 callback 專屬相位
 │    check     │                     （緊接在 poll 之後）
 └──────┬───────┘
        ▼
 ┌──────────────┐  ⑥ close            close 事件的 callback
 │    close     │                     （如 socket.on('close', …)）
 └──────┬───────┘
        └──────────────► 回到 ① 開始下一圈
```

逐相位拆開——只挑你後端天天踩到的講，idle/prepare/pending 多半是 libuv 內部的事，你寫的程式碼幾乎不直接落在那裡：

- **① timers**：這一圈走到這裡時，libuv 看「現在時間」，把所有**已到期**的 `setTimeout` / `setInterval` callback 撈出來跑。注意關鍵字是「已到期」——`setTimeout(fn, 100)` 的意思**不是「100ms 後準時跑 fn」**，是「**最早在 100ms 後、且要等 loop 下一次走到 timers 相位時，才會跑 fn**」。如果 loop 正卡在別的相位（某個 callback 跑很久），就算 100ms 早就過了，fn 也得等 loop 轉回 timers 相位才跑。**這就是你 ch09 抱怨的「`setTimeout` 不精確」的相位級根因**：延遲只保證下界（不早於），不保證上界（可能晚很多，取決於 loop 多忙）。

- **④ poll（I/O）**：這是整顆 loop 的核心，也是它「不停下來等」那句紀律的所在。poll 相位做兩件事：(1) 跑那些**已經完成的 I/O** 的 callback（你的資料庫查詢回來了、socket 收到一包資料了、檔案讀完了）；(2) 如果暫時**沒有**已完成的 I/O、也沒有別的事要做，loop 就**阻塞在 poll 相位**，向 OS（epoll/kqueue/IOCP）說「有任何 I/O 好了就叫醒我」，然後**真的睡著**——不燒 CPU 地等。這就是 Node 能掛 3,200 條閒置連線卻幾乎不耗 CPU 的祕密：沒事的時候它真的在睡，OS 幫它盯著所有 fd。

- **⑤ check**：`setImmediate(fn)` 的 callback 專門在這裡跑，**緊接在 poll 之後**。`setImmediate` 的字面意思（「立即」）有誤導性——它不是「馬上」，是「**這一圈的 poll 跑完後、在 check 相位跑**」。它的價值在於「**在當前這一圈的 I/O 處理完之後、但在進入下一圈的 timers 之前**」插隊執行，這個時機非常明確，下面 worked example 會用到。

- **⑥ close**：`socket.on('close', …)`、`emitter.on('close', …)` 這類關閉事件的 callback。連線斷掉的善後跑在這裡。

把這張圖記牢，你就能回答上面所有問題了。但這張圖**還缺一塊**——它只畫了「相位之間」的大格子，沒畫「相位的縫隙裡」還有一層更急的東西在插隊。那就是 microtask。

## microtask：在每個縫隙裡插隊清空的兩條隊伍

相位佇列（timers、poll、check…）裡裝的東西，統稱 **macrotask**（巨集任務）——一圈處理一個相位的一批。但在 Node 裡，還有兩條**優先級更高**的隊伍，它們不屬於任何相位，而是**在每一個 macrotask 跑完之後、loop 還沒往下走之前，被強制清空（drain）**。這兩條就是 **microtask**（微任務）：

1. **`process.nextTick` 佇列**（Node 特有，不是 V8 的）——優先級**最高**。
2. **Promise microtask 佇列**（V8 的，`.then` / `.catch` / `await` 之後的續行、`queueMicrotask`）——次高。

清空的規則，精確記住這幾條（2026-06，以 Node 官方文件與 V8 行為為準）：

- **時機**：每跑完**一個** macrotask callback（不是一整個相位、是一個 callback），loop 就停下來，**先把兩條 microtask 隊伍徹底清空**，才去跑下一個 macrotask。相位與相位**之間**的切換點，也會清空。
- **兩條的先後**：清空時**先把 `nextTick` 佇列整個清乾淨，再清 Promise microtask 佇列**。
- **「徹底清空」是遞迴的**：清 microtask 的過程中如果**又產生了新的 microtask**，那些新的也得在同一輪清掉——直到兩條隊伍**都空**，才放行下一個 macrotask。這條「遞迴清到空」是後面「餓死 I/O」陷阱的根。

把它疊到剛才那張相位圖上，完整的一圈長這樣（用文字描述，避免圖太密）：

```
跑 timers 相位的一個 callback
   → 清空 nextTick 佇列（含過程中新產生的）
   → 清空 Promise microtask 佇列（含過程中新產生的）
跑 timers 相位的下一個 callback
   → 又清空 nextTick → 又清空 Promise microtask
   …timers 相位的 callback 跑完…
進 poll 相位，跑一個 I/O callback
   → 清空 nextTick → 清空 Promise microtask
   …如此類推，每個 macrotask 後面都黏著一次「清空兩條 microtask」…
```

> **我以為 vs 實際。** 你大概把 `process.nextTick`、`Promise.then`、`setTimeout(fn,0)`、`setImmediate` 都當成「延後一下執行」的同義詞，憑感覺挑一個用。實際上它們**落在四個完全不同的優先級層**：`nextTick`（最急，microtask 第一順位）＞ `Promise.then`（microtask 第二順位）＞ `setTimeout(fn,0)`（macrotask，timers 相位）＞`setImmediate`（macrotask，check 相位）。前兩者在**每個 macrotask 的縫隙**就被清空，後兩者要**等 loop 轉到對應相位**才跑。混用它們而不懂這個層級，就會寫出「為什麼這行比那行晚跑」的 bug——下面 worked example 就是在追這個。

### Worked example：手追一段混合輸出的順序

這是本章必須親手走一遍的推演。給你一段程式，**不准背答案，要從相位推**。

```
// ⚠️ 這是 CommonJS 模組（用 require/main script 起跑）。
//    ESM（import / top-level await）的起跑路徑不同，頂層 nextTick 與
//    Promise 的相對順序可能不一樣——這個 caveat 下面解答會說。
const fs = require('fs');

console.log('A: 同步開始');

setTimeout(() => console.log('B: setTimeout 0'), 0);

setImmediate(() => console.log('C: setImmediate'));

Promise.resolve().then(() => console.log('D: Promise.then'));

process.nextTick(() => console.log('E: nextTick'));

fs.readFile(__filename, () => {
  console.log('F: readFile callback（I/O 完成，在 poll 相位）');
  // 以下三行是在「I/O callback 內部」排程的——這是順序變確定的關鍵
  setTimeout(() => console.log('G: setTimeout 0（在 I/O 內排）'), 0);
  setImmediate(() => console.log('H: setImmediate（在 I/O 內排）'));
  process.nextTick(() => console.log('I: nextTick（在 I/O 內排）'));
});

console.log('J: 同步結束');
```

先自己推，再看解答。

### 推演解答

**輸出順序（CommonJS）**：
```
A: 同步開始
J: 同步結束
E: nextTick
D: Promise.then
B: setTimeout 0          ← B 與 C 的相對順序見下方 caveat
C: setImmediate
F: readFile callback
I: nextTick（在 I/O 內排）
H: setImmediate（在 I/O 內排）
G: setTimeout 0（在 I/O 內排）
```

一步步推，這才是重點——你要**講得出每一步為什麼**：

**第一階段：同步主程式碼跑完。** `A` 和 `J` 是頂層同步 `console.log`，最先跑、按書寫順序。中間那些 `setTimeout` / `setImmediate` / `Promise.then` / `nextTick` / `readFile` 全部只是**登記**——把 callback 排進各自的隊伍，不當場執行。所以同步階段只印 `A`、`J`。

**第二階段：同步碼一跑完，立刻清 microtask（在進入任何相位之前）。** 規則：先 `nextTick`、再 Promise。所以 `E: nextTick` 先印，`D: Promise.then` 後印。**這就是為什麼 `E` 在 `D` 前面、又都在所有 `setTimeout`/`setImmediate` 前面**——microtask 的優先級高於任何 macrotask 相位。

**第三階段：進入相位循環。**
- `setTimeout(…,0)` 在 timers 相位、`setImmediate` 在 check 相位、`readFile` 的 callback 在 poll 相位。
- 頂層的 `B`（timers）與 `C`（check）誰先？**這是非確定的**——見下方 caveat。圖上我寫 `B` 在 `C` 前只是其中一種可能。
- `F`（readFile 的 I/O callback）在 poll 相位跑。檔案讀完通常要一點時間，所以 `F` 排在 `B`、`C` 之後。

**第四階段：I/O callback 內部排的三個——這裡順序變確定了。** `F` 印完後，緊接著清 microtask：`I: nextTick` 先（microtask 第一順位）。然後 loop 從 poll 相位繼續往下走——**下一個相位是 check**，所以 `H: setImmediate` 先跑。`G: setTimeout 0` 屬於 timers 相位，要等 loop **再轉一整圈回到 timers** 才跑，所以 `G` 最後。**順序固定是 I → H → G。**

**為什麼「在 I/O callback 內部」`setImmediate` 一定先於 `setTimeout`？** 因為此刻 loop 正站在 poll 相位（剛跑完 I/O callback），它往下走的下一站就是 check（`setImmediate` 的家），而 timers（`setTimeout` 的家）在它**後面一整圈**。所以在 I/O callback 裡，`setImmediate` 永遠贏 `setTimeout`——這是**確定**的。

**⚠️ caveat 一（頂層 B vs C 非確定）**：在**頂層**（不是 I/O callback 內）同時排 `setTimeout(…,0)` 和 `setImmediate`，誰先跑**不保證**。原因：`setTimeout(…,0)` 的延遲會被 clamp 到最小值（約 1ms），而程式從啟動到第一次走到 timers 相位耗時多少是不定的——如果那段時間 ≥ 1ms，timers 相位發現計時器已到期，`B` 先；如果 < 1ms，計時器還沒到期，loop 滑過 timers、先到 check 跑 `C`。所以頂層這兩個的相對順序**靠機器當下的速度決定**，不要寫程式去依賴它。（要確定，就把它們放進一個 I/O callback 內——如第四階段，順序立刻固定。）

**⚠️ caveat 二（CommonJS vs ESM）**：上面整個推演假設這是 **CommonJS**（`require` / 傳統 main script）。若是 **ESM**（`.mjs` / `import` / top-level await），頂層程式碼的起跑經過不同的求值路徑，**頂層的 `nextTick` 與 Promise 的相對順序可能改變**（同一段碼換成 ESM 可能印出不同順序）。本書不深究這個邊角，但你要知道「同一段碼在 CJS 與 ESM 下輸出可能不同」這件事存在——面試被追問時這是加分點。

**常見錯路**：(a) 以為 `setImmediate`（名字像「立即」）會最先跑——錯，它在 check 相位，連 microtask 都排在它前面。(b) 以為頂層 `setTimeout(…,0)` 一定先於 `setImmediate`——錯，頂層是非確定的。(c) 忘了「**每個** macrotask 後面都黏著一次 microtask 清空」，於是漏算了 `I` 為什麼緊跟在 `F` 後面。把這三個錯避開，你就不是在背順序，是在**推**順序。

## process.nextTick 餓死 I/O：把急救藥當飯吃

上一節埋了一個地雷：microtask「**遞迴清到空才放行下一個 macrotask**」。現在引爆它。

`process.nextTick` 是**最高優先級**的隊伍，且 loop **必須把它清到完全空**才能往下走。問題來了——如果一個 `nextTick` callback 裡面**又排了一個新的 `nextTick`**呢？

```
function loopForever() {
  process.nextTick(loopForever);   // 每次 nextTick 裡又排一個 nextTick
}
loopForever();
```

這條鏈**永遠清不空**：清第一個 nextTick → 它排了第二個 → 為了「清到空」得清第二個 → 它又排了第三個 → ……loop **永遠卡在「清 nextTick 佇列」這一步，一次都進不到 timers、進不到 poll**。後果是災難級的：

- 你所有的 `setTimeout` / `setInterval`**永遠不觸發**（卡在 timers 之前）。
- 你所有的網路 I/O——**新連線進不來、已連線的請求收不到資料、回應送不出去**——因為 loop 永遠到不了 poll 相位。你的 HTTP server 對外看起來像**整個死掉**，但 CPU 是 100%（忙著清 nextTick），不是 0%。這個徵兆極具迷惑性：機器「很忙」卻「什麼都不回」。

這就叫 **I/O 餓死（starvation）**。注意它和 ch05 那種「同步重運算卡住」的**症狀一樣**（單核 100%、所有請求乾等），但**機制不同**：ch05 是「一個 callback 跑太久不讓出」；這裡是「callback 們各自都很快、但它們用 nextTick 無限續命，讓 loop 永遠出不了 microtask 清空階段」。兩者都殺死 event loop，但一個是「跑太久」，一個是「插隊插到底」。

實務上你不會手寫 `loopForever`，但**遞迴用 `nextTick` 來「分批處理大量資料」**是真實會踩的雷——「我每處理一筆就 `nextTick` 排下一筆，這樣不會卡住吧」——錯，這正是餓死 I/O 的標準寫法。

> **我以為 vs 實際。** 你大概把 `process.nextTick` 當成「`setTimeout(fn, 0)` 的更快版」在用。實際上它們是兩個世界：`setTimeout(fn,0)` 是 **macrotask**，排在 timers 相位，**會讓 loop 繼續轉**（跑完一輪 I/O 才回來跑它），所以用它分批處理大量資料**不會**餓死 I/O；`nextTick` 是 **microtask 第一順位**，**會在 loop 往下走之前插隊清空**，遞迴用它就會把 loop 釘死。Node 官方的建議很直白：`nextTick` 是給「**同一個 tick 內、在 loop 繼續之前必須做的緊急善後**」用的（例如在事件觸發前先確保某狀態就緒、或統一錯誤的非同步拋出時機）——它是急救藥，不是排程工具。**要把工作延後又不餓死 I/O，用 `setImmediate`**（check 相位，macrotask，會讓 loop 轉一圈），這是「延後執行」場景的安全預設。

## thread pool：哪些東西其實不在主執行緒上

到這裡你已經知道「你的 JS 跑在唯一一條執行緒上」。但 ch05 也提過一句你可能還沒消化的話：**libuv 底下有一個 thread pool（執行緒池），預設 4 條**。這兩件事不矛盾——關鍵是搞清楚「什麼用 pool、什麼不用，以及為什麼網路 I/O 偏偏不用」。

`UV_THREADPOOL_SIZE` **預設 4**（2026-06，libuv 文件；可調，上限 1024）。這 4 條背景執行緒，給的是**那些 OS 沒有提供好用的非同步介面、只能用阻塞式 API 的操作**——libuv 只好開背景執行緒去阻塞地跑它們、跑完再把結果送回主 loop 的 poll 相位。落在 thread pool 上的，主要是這四類（2026-06，libuv 文件）：

- **`fs.*` 檔案操作**（讀檔、寫檔、stat…，除了 FSWatcher）。
- **`dns.lookup()`**（注意：是 `getaddrinfo` 那條路，即 `dns.lookup`；`dns.resolve*()` 走 c-ares、本身非同步，**不**佔 pool）。
- **async crypto**（`crypto.pbkdf2`、`scrypt`、`randomBytes` 之類算很久的）。
- **所有 async zlib**（壓縮/解壓縮）。

**而網路 I/O——TCP、UDP、你那 3,200 條 WebSocket 的收發——不走 thread pool**。它走的是 OS 自己的非同步 I/O 原語：Linux 的 **epoll**、macOS/BSD 的 **kqueue**、Windows 的 **IOCP**。這些原語讓「同時盯住上萬個 socket、誰有資料了就通知我」這件事**在 OS 核心層**就高效完成，不需要每條連線配一條執行緒。libuv 直接把這件事交給 OS，在主 loop 的 poll 相位收成果。

**為什麼這個區分重要？** 因為它決定了「什麼東西會搶 thread pool 的 4 條執行緒、什麼不會」，而 thread pool 只有 4 條、會排隊：

```
┌─────────────────────────────────────────────────────┐
│ event loop（單一執行緒，跑你所有 JS）               │
└───────────────────────┬──────────────────────────┬──┘
       需要背景阻塞     │             OS 原生非同步│
                        ▼                          ▼
              ┌───────────────────┐    ┌───────────────────────┐
              │ libuv thread pool │    │ OS：epoll/kqueue/IOCP │
              │ （預設 4 條）     │    │ TCP/UDP/WebSocket 收發│
              │ fs / dns.lookup / │    │ ← 你的 3,200 連線在這 │
              │ crypto / zlib     │    │ 不佔 thread pool      │
              └───────────────────┘    └───────────────────────┘
        4 條滿了就排隊                  連線數受 OS fd 上限不受 4 限
```

把這張圖記牢，三個你大概沒連起來的事就通了：

1. **為什麼網路連線數不被「4」限制**：3,200 條 WebSocket 不佔那 4 條執行緒——它們在 epoll 那側。所以你能掛 3,200 條（甚至上萬條）連線，瓶頸是 OS 的 fd 上限與記憶體，不是 thread pool。如果網路 I/O 走 thread pool，4 條執行緒只能同時服務 4 條連線，Node 的高並發神話當場破滅——**這就是為什麼 libuv 一定要把網路交給 epoll**。
2. **`UV_THREADPOOL_SIZE=4` 什麼時候會咬你**：如果你的服務**同時**發起大量 `fs` 讀寫、或大量 `crypto.pbkdf2`（例如登入尖峰一堆密碼雜湊），這些會塞滿那 4 條執行緒，**第 5 個之後排隊**——你會看到「檔案讀取/密碼雜湊的延遲莫名變長，但 CPU、網路都沒滿」。這時候調大 `UV_THREADPOOL_SIZE`（或把 CPU 重的 crypto 改架構）才對症。
3. **「不阻塞」也分兩種**：一個 `await fs.readFile(...)` 不阻塞**你的 event loop**（它在背景執行緒讀、loop 空出來服務別人），但它**會佔用一條 thread pool 執行緒**；一個 `await fetch(...)` 連 thread pool 都不佔（走 epoll）。兩個都「非阻塞」，但消耗的資源不同——這個分辨在你調效能時是真金白銀。

> **我以為 vs 實際。** 你大概記成「Node 的非阻塞 I/O 靠那個 thread pool」。一半對一半錯：**檔案/DNS/crypto/zlib 靠 thread pool（預設 4 條，會排隊）；但網路 I/O——你後端最大宗的 I/O——根本不碰 thread pool，靠 OS 的 epoll/kqueue/IOCP**。把這兩條路混為一談，你就會在「網路慢」時去調 `UV_THREADPOOL_SIZE`（白調），或在「檔案/雜湊慢」時去找網路問題（白找）。

## 什麼殺死 event loop——以及怎麼救

把前面所有機制收束成一個實用結論：**event loop 的死法只有一種本質——有東西讓那條唯一的執行緒長時間出不來（不論是「跑太久不讓出」還是「插隊插到底」），於是 poll 相位永遠輪不到，所有 I/O 凍結。** 具體的兇手有幾類：

**1. CPU 密集同步工作（最常見，ch05 的病例）。** 一個沒有 `await` 的大迴圈、一段同步的重運算。它在跑的時候不讓出，loop 卡在它身上。回指 ch05：那次你抓出的就是這型。

**2. 巨大的 `JSON.parse` / `JSON.stringify`。** 這是上一型的特例，但常被漏掉因為它「看起來只是一行」。`JSON.parse` 是**同步**且 **O(n)**——n 是字串長度。一個幾 MB 的 JSON（一個沒設大小上限的 `req.body`、一個從上游撈來的大回應），parse 它就是幾十到幾百毫秒的同步阻塞。它危險在「**藏在一行裡、且 n 由外部輸入決定**」——你信任了輸入的大小，它就是一顆定時炸彈（這正是「相信所有輸入都可能異常大」的理由）。

**3. 同步版的 crypto / 同步檔案 API。** `crypto` 的同步版（如同步的 `pbkdf2Sync`、`scryptSync`）、`fs.readFileSync` 這類 `*Sync` API——它們**不走 thread pool**，直接在主執行緒上阻塞地跑。在啟動腳本裡用 `readFileSync` 讀個設定檔沒問題（那時沒有並發請求），但**在 hot path 用任何 `*Sync` API 都是在主執行緒上引爆**。

**4. 遞迴 `process.nextTick`（上一節）。** 每個 callback 都很快，但用 nextTick 無限續命，loop 永遠清不空 microtask、出不了門。

對策——按「這個重活的本質」分流，這是判準不是口號：

| 重活的本質 | 對策 | 為什麼 |
|---|---|---|
| 可以切成小塊的大迴圈/大批資料 | **分片讓出**：每處理一批，`await` 一個 `setImmediate`（**不是 `nextTick`**）讓 loop 轉一圈 | `setImmediate` 是 macrotask、會讓 loop 跑一輪 I/O 再回來，所以分片之間 loop 能服務別人、I/O 不餓死 |
| 真正 CPU 密集、切不開（影像處理、複雜計算、大 JSON） | **丟 `worker_threads`** | worker 是**真正的另一條 OS 執行緒**，在別的核心上跑，完全不碰主 loop——這是 Node 裡唯一的「真平行」逃生口（實作細節本章不展開） |
| 重活根本不該在這個請求路徑做 | **丟出去**：推進佇列（SQS、BullMQ）給別的 worker 行程/服務非同步處理 | 把同步重活從「擋著回應的 hot path」搬到「離線可慢慢做的地方」——你 ch04 結算 pipeline、ch09 job queue 就是這個思路 |
| 大 `JSON.parse` | 串流式解析、或先擋住輸入大小上限 | 不要一次性 parse 一個無上限的字串；把 O(n) 的 n 控制住 |

注意第二列那個關鍵字：**`worker_threads` 是 Node 裡唯一能用滿多核的方法**。event loop 本身只用得到一核（單執行緒），所以一台 8 核機器跑單一 Node 行程，CPU 密集工作只用得到 1/8 的算力。要用滿多核，要嘛開 `worker_threads`、要嘛開多個 Node 行程（cluster / 多 pod，每個各占一核）。這就引出最後一節的取捨。

## 對照 OS 多執行緒：你換到了什麼、放棄了什麼

退一步，把 event loop 這種並發模型，跟你熟悉的 OS 多執行緒（Java、Go 的某些用法）並排，看清這筆交易的兩面。

**event loop（單執行緒並發）換來的：**

- **沒有共享狀態的鎖、沒有 race condition（在單一 loop 內）。** 因為任何時刻只有一個 callback 在跑、不搶占，你**不會**遇到「兩條執行緒同時改一個變數改壞了」這種 data race。你寫 `counter++` 不用加鎖——在多執行緒語言裡這一行可能是 bug（非原子），在 Node 的單一 loop 裡它是安全的。這省掉了整整一個類別的並發 bug（深層的並發正確性形式化證明見《把系統寫成定理》tla 書）。
- **極低的並發成本。** 掛一條閒置連線只要幾 KB（一個 socket 物件 + 在 epoll 裡登記一個 fd），不像 thread-per-connection 每條吃一條執行緒的 stack（MB 級）。這就是一台機器扛 3,200 連線（甚至上萬）的本錢。

**放棄的：**

- **用不滿多核。** 單一 event loop 只跑在一核上。8 核機器、CPU 密集工作，你只用得到 1/8（除非開 worker_threads / 多行程）。對 I/O 密集服務這無所謂（瓶頸是等待不是算力）；對 CPU 密集服務這是硬傷。
- **沒有搶占＝一個壞公民拖垮全場。** 多執行緒模型裡，OS 排程器會強制輪流——一條執行緒卡死，別條照跑（最多那一核被佔）。event loop 沒有這個保護網：一個 callback 不讓出，**所有人**一起死。你的容錯從「OS 幫你隔離」變成「**全靠每個 callback 自律地讓出**」。這是 ch05 整章、本章半章在講的那個死穴。
- **race 沒消失，只是換了長相。** 「單一 loop 內無 data race」不代表「沒有並發 bug」。跨越 `await` 的邏輯仍可能交錯出問題——你 `await` 一個操作時 loop 跑了別人的 callback，回來時世界已經變了（這種「`await` 之間的狀態被別人改掉」的競態，是 Node 真實會有的 bug，只是它不是 CPU 暫存器層的 data race，而是邏輯層的交錯）。所以「Node 沒有並發問題」是**錯的**——它只是把並發問題從「鎖與 data race」換成「`await` 邊界的邏輯交錯」。

```
            event loop（單執行緒並發）          OS 多執行緒（平行）
 鎖/race    無 data race（單 loop 內）          要鎖、有 data race
 多核       用不滿（單核，除非 worker/多行程）  天生用滿多核
 連線成本   極低（幾 KB/連線）                  高（一條執行緒/連線，MB 級）
 容錯       無搶占→一個卡死全死                 OS 搶占→一條卡死別條照跑
 適用       I/O 密集（等多算少）                CPU 密集（算多等少）
```

**這就是當年那個決定的真相**：你選 Node 建這些後端，等於選了「I/O 密集場景下用最少資源扛最多連線，代價是把『不讓 callback 跑太久』的紀律扛在自己肩上」。對你那些 I/O 密集的服務（即時通知、API 後端——大多在等資料庫、等 socket），這筆交易**划算到不行**。它唯一會反咬你的，就是哪天有人在 hot path 塞了個 CPU 密集的同步重活——那一刻你才會痛感「沒有搶占」的代價。**理解這顆 loop，本質上就是理解你這六年所有後端服務共享的那個並發合約：你用『等得有效率』換『算不了重活』，並親自擔保每個 callback 都守規矩讓出。**

## 故障模式與防禦

把這顆 loop 會怎麼死，攤成「會怎麼壞 / 壞了長什麼樣 / 怎麼防」。每個都能對回你做過的系統。

| 故障 | 會怎麼壞 | 壞了長什麼樣（可觀測徵兆） | 怎麼防 |
|---|---|---|---|
| **同步重運算卡 loop**（ch05 病例，綁 NeoBards 剖析） | 一行同步 CPU 密集（大迴圈、`*Sync` API、同步 crypto）釘住唯一執行緒，poll 相位輪不到，所有 I/O 凍結 | 單核 100%（其他核閒）、**event loop lag 飆數百 ms**、p99/p999 爆炸而 p50 還行、健康檢查逾時被踢出輪替 | hot path 嚴禁同步重活與 `*Sync` API；可切的分片＋`setImmediate` 讓出；切不開的丟 `worker_threads`；量 event loop lag 當第一線指標 |
| **巨大 JSON.parse/stringify** | 同步 O(n)，n 由外部輸入決定（無上限 `req.body`、大上游回應），藏在一行裡 | 偶發性 event loop lag 尖刺，與「剛好來了一個大 payload」時間吻合；難重現因為要大輸入才觸發 | 擋住輸入大小上限（別信任 payload 大小）；大資料用串流式解析；把大 JSON 處理移出 hot path |
| **遞迴 process.nextTick 餓死 I/O** | nextTick 無限續命，loop 永遠清不空 microtask、進不了 poll，**新連線進不來、舊請求收不到** | 單核 100% 但「整個 server 像死了、什麼都不回」（CPU 忙、零回應，極具迷惑性）；`setTimeout` 也永不觸發 | 分批/延後工作一律用 `setImmediate`（macrotask）不用 `nextTick`（microtask）；`nextTick` 只留給同 tick 緊急善後 |
| **thread pool（4 條）被打滿** | 大量並發 `fs`/`dns.lookup`/`crypto`/`zlib` 塞滿預設 4 條執行緒，第 5 個起排隊 | **檔案/DNS/密碼雜湊延遲變長，但 CPU、網路都沒滿**（瓶頸藏在那 4 條）；調大 pool 後緩解＝確診 | 調大 `UV_THREADPOOL_SIZE`、或把 CPU 重的 crypto 改架構；別把「網路慢」誤診成 thread pool 問題（網路不走 pool） |
| **`await` 邊界的邏輯交錯**（並非 data race） | 兩個請求各自 `await` 時 loop 跑了對方的 callback，回來時共享狀態已被改（「檢查—再行動」中間被插隊） | 偶發、難重現的資料不一致（庫存超賣、重複扣款），只在並發夠高時出現；單測抓不到 | 把「檢查＋行動」之間別跨 `await`，或用資料層的原子操作/唯一約束兜底（這正是 ch10 冪等、ch03 鎖在解的問題） |

通用的「複雜系統為什麼會崩」分類（雪崩、metastable failure 跨領域通論）見《正常意外》（fail）；過載時延遲為什麼「無限長」的數學（把 event loop 當 processor-sharing 近似、ρ→1 爆炸）見《等待的數學》（queue）。這裡的故障**綁定的是你這顆 loop 具體會怎麼凍住**。

## 紙上推演

純觀念深掘，不寫可執行碼；下面的程式片段只用來追相位邏輯。

**[15 分鐘] ★★ 排出混合 microtask / macrotask 的執行順序。**
下面是 CommonJS 主程式。寫出輸出順序，並對每一行**講出它落在哪個層級／相位、為什麼排在那個位置**。

```
console.log('1');
setImmediate(() => console.log('2'));
Promise.resolve().then(() => console.log('3'));
process.nextTick(() => {
  console.log('4');
  process.nextTick(() => console.log('5'));  // nextTick 裡又排一個 nextTick
});
setTimeout(() => console.log('6'), 0);
console.log('7');
```

### 推演解答

**輸出：`1, 7, 4, 5, 3, 6, 2`**（`6` 與 `2` 的相對順序見下方但書）。

- **`1`、`7`**：頂層同步 `console.log`，最先、照書寫順序。中間的 `setImmediate`/`Promise.then`/`nextTick`/`setTimeout` 都只是登記。
- **`4`**：同步碼跑完，立刻清 microtask；`nextTick` 是第一順位，所以 `4` 在 Promise 的 `3` 之前。
- **`5`**：關鍵點——`4` 的 callback 裡**又排了一個 `nextTick`**。規則是「nextTick 佇列要清到**完全空**才放行」，所以這個新排的 `5` **在同一輪 microtask 清空裡就被處理掉**，不會等到下一圈。`5` 緊跟 `4`。（如果這裡是無限遞迴排 nextTick，loop 就永遠卡在這步——這就是餓死 I/O。）
- **`3`**：nextTick 佇列終於清空，才輪到 Promise microtask 佇列。
- **`6`**（setTimeout，timers 相位）與 **`2`**（setImmediate，check 相位）：兩個都是 macrotask，要等 loop 進入相位循環。**它倆的相對順序在頂層是非確定的**（取決於啟動到第一次 timers 相位是否已過那 ~1ms clamp）。多數情況 `6` 先（timers 在 check 前），但別依賴它。

**常見錯路**：(a) 漏掉 `5` 必須在這一輪就清掉（以為 nextTick 裡排的 nextTick 會留到下圈）——它不會，「清到空」是遞迴的。(b) 以為 `setImmediate`（名字像「立即」）會很早跑——它在 check 相位，比所有 microtask 都晚。

---

**[15 分鐘] ★★ 三個工作，各該放主執行緒 / thread pool / worker_threads？**
判斷下面三個工作，在 Node 後端裡各**自然落在哪裡**（或**該被搬到哪裡**），並說為什麼。

- **甲**：處理一個 HTTP 請求——查一次 PostgreSQL、組個 JSON、回傳。
- **乙**：使用者上傳一張圖，要在伺服器端把它縮成三種尺寸（純 CPU 的影像運算，每張約 800ms）。
- **丙**：登入時把使用者密碼用 `crypto.pbkdf2`（async 版）做雜湊比對。

### 推演解答

- **甲＝主執行緒（event loop）就好，且這正是它的主場。** 整個流程是 I/O 密集：查 PG 是網路 I/O（走 epoll，不佔 thread pool）、組 JSON 與回傳是輕量同步。`await db.query` 時 loop 空出來服務別人，這就是 event loop 最划算的場景。**不要**為它開 worker——沒有 CPU 重活，開 worker 只是徒增成本。
- **乙＝必須丟 `worker_threads`（或外部服務）。** 影像縮放是**純 CPU、800ms、切不太開**的同步重活——放主執行緒就是 ch05 災難（一張圖卡死整台 800ms）；它也**不該走 thread pool**（thread pool 是給 libuv 的 fs/dns/crypto/zlib，不是給你的任意 JS 計算）。worker_threads 是真正的另一條 OS 執行緒、在別的核心上跑，把這 800ms 的 CPU 重活搬出主 loop。規模再大就丟出去成一個獨立的影像處理服務（ch04 那種離線 pipeline 思路）。
- **丙＝async `pbkdf2` 自動走 thread pool，通常不用你管——但要小心 4 條的上限。** async crypto（`pbkdf2`/`scrypt`）是 libuv 明確放進 thread pool 的四類之一，所以它**不卡 event loop**（在背景 4 條執行緒上算）。平常沒事；但**登入尖峰**——一堆人同時登入、一堆 `pbkdf2` 同時發起——會塞滿那 4 條執行緒，第 5 個起排隊，你會看到「登入延遲在尖峰莫名變長」。對策：調大 `UV_THREADPOOL_SIZE`，或把雜湊搬到專門的 auth 服務。**注意絕對不能用同步版 `pbkdf2Sync`**——那個不走 thread pool，直接在主執行緒上阻塞，一次登入就卡死整台。

**常見錯路**：(a) 把乙（純 CPU 計算）以為「丟 thread pool 就好」——thread pool 不接你的任意 JS 計算，只接 libuv 的那四類 I/O，純 CPU 計算的逃生口是 worker_threads。(b) 用同步版 crypto/fs API 圖方便——`*Sync` 不走 thread pool，是主執行緒殺手。

---

**[20 分鐘] ★★★ 找出「用 Promise 包了、但其實還是阻塞」的假非同步。**
有人說「我把那個重運算用 Promise 包起來了，所以它非同步、不會卡 event loop」。下面是他的寫法（示意）。判斷它**到底卡不卡 event loop**，講清楚為什麼，並說怎麼改才真的不卡。

```
function processHuge(data) {
  return new Promise((resolve) => {
    // data 有上百萬筆，這個 reduce 是純同步的重運算
    const result = data.reduce((acc, item) => acc + heavySyncCompute(item), 0);
    resolve(result);
  });
}

// 呼叫端
await processHuge(massiveArray);   // 「我 await 了，所以它非同步吧？」
```

### 推演解答

**它照樣卡死 event loop。`Promise` 與 `await` 完全沒幫上忙。**

**為什麼**：`Promise` 只是一個「**結果稍後會有**」的容器，它**本身不會把同步運算搬到別的執行緒、也不會自動切片讓出**。看 `new Promise(executor)` 裡那個 executor 函式——它是**同步立即執行**的。所以 `data.reduce(...)`（上百萬筆的純同步重運算）在 `new Promise(...)` 的當下就**同步地、完整地**跑完了，跑的時候**沒有任何 `await` 把控制權交回 event loop**。`resolve(result)` 只是在這坨同步運算**跑完之後**才標記 Promise 完成。

呼叫端的 `await processHuge(...)` 也救不了：`await` 是「**等這個 Promise 完成**」，但這個 Promise 是在那坨同步 reduce **跑完才** resolve 的——所以 `await` 等到的，是一個**已經在主執行緒上阻塞跑完了重運算**的結果。`await` 讓出的時機在重運算**之後**，不是之中。整段期間，event loop 被那個 reduce 釘死。

**這就是「假非同步」的指紋**：包了 `Promise`、用了 `await`，看起來很非同步，但**裡面沒有任何真正的非同步操作（真 I/O、或真的讓出點）**——同步重運算被一層 Promise 糖衣裹著，糖衣不改變它同步阻塞的本質。判準永遠是那句老話：**「這段在跑的時候，有沒有東西把 event loop 還回去？」** 這裡沒有，所以它卡。

**怎麼改才真的不卡**（按重活本質分流，呼應前面那張對策表）：

1. **若 `reduce` 可分片**：把上百萬筆切成一批批（比如每 1 萬筆一批），每批之間 `await new Promise(r => setImmediate(r))` 讓 loop 轉一圈、服務別人，再處理下一批。這樣每批之間 event loop 是活的，I/O 不會凍。**注意要用 `setImmediate` 不是 `nextTick`**——`nextTick` 會餓死 I/O（前面餓死那節的教訓）。
2. **若真的切不開、就是 CPU 密集**：丟 `worker_threads`——把 `processHuge` 整個搬到一條真正的 worker 執行緒上跑，主 loop 完全不碰它，這才是真平行。
3. **若這活根本不必擋著回應**：丟進佇列（BullMQ/SQS）給別的 worker 行程離線處理（ch04/ch09 思路）。

**常見錯路**：(a) 以為「`async`/`Promise`/`await` ＝ 非同步 ＝ 不阻塞」——錯，它們只是**等待非同步結果的語法**，本身不製造非同步、不切片、不換執行緒。一段 `async` 函式裡的純同步迴圈，阻塞起來和普通同步碼一模一樣。(b) 以為「包了 Promise 就會丟到背景跑」——`Promise` 沒有「背景」，executor 是同步跑的；真正能跑到背景的是 worker_threads（另一條執行緒）或 libuv 自己的 thread pool I/O（你的 JS 計算進不去那裡）。

## 自我檢核

口頭自答，講得清楚才算過關：

1. 「並發」和「平行」差在哪？為什麼說 Node 的 event loop 是並發但不是平行？它賣的到底是「算得快」還是別的東西——用「等得有效率」這個角度講一遍。
2. 不靠背、用相位推：`setTimeout(fn, 0)`、`setImmediate`、`Promise.then`、`process.nextTick` 這四個的執行優先級從高到低是什麼？哪兩個是 microtask、哪兩個是 macrotask、各落在哪個相位/隊伍？
3. `setTimeout(fn, 100)` 為什麼不保證在 100ms 整準時觸發、只保證「不早於」？這個延遲是從哪個相位、哪個機制漏出來的（回指你 ch09 對 setTimeout 不精確的抱怨）？
4. 為什麼遞迴 `process.nextTick` 會「餓死 I/O」？它的徵兆（單核 100% 但 server 完全不回應）和 ch05 那種「同步重運算卡住」的徵兆一樣，但機制哪裡不同？要延後工作又不餓死 I/O，該用哪個、為什麼？
5. 你的 3,200 條 WebSocket 的網路收發，走的是 libuv thread pool 還是 OS 的 epoll/kqueue？為什麼**一定**不能讓網路 I/O 走 thread pool（提示：4 條）？反過來，什麼操作才走那 4 條執行緒？
6. `UV_THREADPOOL_SIZE` 預設多少？什麼徵兆會讓你判斷「是 thread pool 被打滿了」而不是別的瓶頸？為什麼「網路慢」時去調這個值是白調？
7. 一個 800ms 的純 CPU 影像處理，為什麼不能放主執行緒、也不能「丟 thread pool」、只能 `worker_threads`？worker_threads 在 Node 的並發圖裡扮演什麼唯一角色（提示：多核）？
8. event loop 這種並發模型，相對 OS 多執行緒，換來了什麼（兩點）、放棄了什麼（兩點）？「Node 沒有並發 bug」這句話為什麼是錯的——`await` 邊界上還會有什麼競態？

## 延伸閱讀

以下連結於 landscape-2026-06 或本章查證（2026-06）：

- **libuv 官方《Design overview》**（docs.libuv.org/en/v1.x/design.html）——相位順序（timers → pending → idle/prepare → poll → check → close）的一手權威來源。讀 "The I/O loop" 那節，把這張相位圖刻進腦子。
- **Node.js 官方《The Node.js Event Loop》**（nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick）——各相位在 Node 語境下處理什麼、`setTimeout` 為什麼不精確、poll 相位怎麼「阻塞地等」。本章相位描述的官方對照版。
- **Node.js 官方《The Node.js Event Loop》之 nextTick 段 + 《Don't Block the Event Loop》**（nodejs.org/learn/asynchronous-work/dont-block-the-event-loop）——`process.nextTick` 為什麼能餓死 I/O、為什麼 `setImmediate` 是延後工作的安全選擇、`JSON.parse` 的 O(n) 危險。讀「nextTick vs setImmediate」與「Blocking the Event Loop」兩段。
- **libuv 官方《Thread pool work scheduling》**（docs.libuv.org/en/v1.x/threadpool.html）——`UV_THREADPOOL_SIZE` 預設 4、哪些操作（fs/dns.lookup/crypto/zlib）走 pool、網路 I/O **不**走 pool 的一手依據。本章 thread pool 那張圖的根。
- **Node.js previous-releases / Release codenames**（nodejs.org/en/about/previous-releases、github.com/nodejs/Release）——確認 active LTS 是 Node 24「Krypton」（自 2025-10-28）、Node 22「Jod」已降為 maintenance（2026-06）。老兵記憶校正用：你腦中若還停在 Node 18/20，這裡更新。
- **延伸到本書他處**：event loop 被同步重運算卡死的**病例與 profiling**（火焰圖怎麼讀、event loop lag 怎麼量）在 ch05；`setTimeout` 撐不住要外部化到持久佇列的故事在 ch09；`await` 邊界的邏輯交錯競態與冪等兜底在 ch10、鎖在 ch03；把 event loop 當 processor-sharing 近似、過載時延遲為什麼炸開的**數學**見《等待的數學》（queue）；並發正確性的形式化證明見《把系統寫成定理》（tla）。
