# Docker：容器隔離的原理

在一台正在跑容器的機器上，挑一個容器，進到它裡面下 `ps aux`。你會看到一個乾淨得不真實的世界：PID 1 是你自己的應用程式，再幾個它生出來的子行程，如此而已。沒有 systemd、沒有 sshd、沒有鄰居容器那幾十個行程。它看起來像一台只跑著你這支程式的全新機器。

現在退回 host，在外面下一次 `ps aux`。剛剛那個「PID 1」此刻是一個 PID 兩萬多的普通行程，和 host 上其他幾百個行程並排躺在同一張表裡，由同一顆 kernel 排程，跑在同一塊實體記憶體上。容器裡的乾淨世界是一場精心安排的錯覺——它不是一台機器，它是 host 上一群被「框住視野」的普通行程。

理解 Docker，要從拆穿這個錯覺開始：**容器不是輕量虛擬機**。VM 是用 hypervisor 虛擬化整套硬體、每台 guest 跑一份自己的完整 kernel；容器底下沒有任何一份額外的 kernel，它就是 host kernel 上的普通行程，只是被 kernel 的幾組原語罩住，讓它「以為」自己獨占一台機器。這個區別不是術語潔癖——它決定了容器啟動為什麼是毫秒級、密度為什麼可以那麼高，也決定了它的隔離邊界在哪裡會破。這一章要把那場錯覺是怎麼造出來的、用什麼造的、又在哪裡會穿幫，一層層拆開。

## 先把問題講難：共用一顆 kernel，憑什麼互不干擾

把「在一台機器上跑很多個互相隔離的工作負載」這件事的需求攤開，你會發現它其實是好幾個獨立的問題綁在一起：

我希望 A 容器列不出 B 容器的行程，更殺不掉它；我希望 A 容器看到的根目錄是它自己那份檔案系統，不是 host 的 `/`；我希望 A 容器有自己的網路堆疊、自己的 IP，綁 80 port 不會撞到 B 也綁 80；我希望 A 容器就算瘋狂吃記憶體，也不會把 B 和 host 一起拖垮；我希望就算 A 裡面跑的程式被打穿了，它能對 host 幹的壞事也有限。

最乾脆的做法當然是給每個工作負載一台真機器，或者退而求其次，一台 VM——各自一份硬體、一份 kernel，物理上就隔開了。但這付出的代價是每跑一份就要開機一份 kernel、配一塊獨立記憶體，啟動數十秒、密度低、開銷大。我們想要的是「VM 那樣的隔離感」配上「普通行程那樣的輕」。

難點正在於這個「配上」。一旦你決定讓所有工作負載**共用同一顆 host kernel**，上面那一串「我希望」就全部失去了物理屏障。同一顆 kernel 的行程表是同一張、檔案系統樹是同一棵、網路堆疊是同一套、記憶體是同一塊。預設情況下，host 上任何一個行程都看得見、（有權限的話）動得了其他所有行程。要在這種「物理上全部相通」的前提下，硬生生切出一塊塊「看起來互相隔離」的世界，你不能靠多開硬體——你只能改變每個行程**看到什麼、能用多少、能做什麼**。

這正好就是 Linux kernel 三組原語各自負責的事，而 Docker 不過是把它們組裝起來的工具：

- **namespace** 管「看得到什麼」——切割每個行程對系統資源的**視野**。
- **cgroup** 管「能用多少」——限制每個行程群組對 CPU、記憶體、I/O 的**額度**。
- **capabilities、seccomp、user namespace** 這一層管「能做什麼」——限制行程能向 kernel 發起的危險動作。

容器，就是「一組 namespace ＋ 一組 cgroup 額度 ＋ 一套權限削減」罩在一群普通行程上的總和。沒有一個叫「容器」的 kernel 物件——kernel 眼裡只有行程、namespace、cgroup。「容器」這個詞是上層工具給這個組合取的名字。

## namespace：切割「看得到什麼」

namespace 的點子簡單到近乎樸素：kernel 裡每一類全域資源——行程編號、掛載點、網路介面、主機名——本來是全機共用的一張表，namespace 讓 kernel 為某一群行程**另開一張同類的表**，從此這群行程只看得到自己那張，看不到別人的。

關鍵在於這是「視野」的切割，不是資料的複製。host kernel 還是那同一顆，行程表底下還是那同一份資料結構；namespace 做的是在 kernel 查詢「這個行程看得到哪些行程」時，按它所屬的 PID namespace 過濾出一個子集合，並且**重新編號**。所以容器裡的應用是貨真價實的 PID 1——在它那張 PID namespace 的表裡，它就是第一個；而在 host 那張全域表裡，它是兩萬多號。同一個行程，兩個身分，取決於你站在哪張表看它。

Linux 到 2026-06 有八種 namespace，各切一類視野（以 `man 7 namespaces` 為準）：

| namespace | 隔離什麼 | clone flag | 容器裡的效果 |
|---|---|---|---|
| pid | 行程 ID | CLONE_NEWPID | 容器內第一個行程是 PID 1，看不到 host 其他行程 |
| net | 網路堆疊 | CLONE_NEWNET | 獨立的網卡、IP、路由表、iptables、port 空間 |
| mnt | 掛載點 | CLONE_NEWNS | 看到自己那份根目錄，不是 host 的 `/` |
| uts | 主機名、domain | CLONE_NEWUTS | `hostname` 改的是容器自己的，不動 host |
| ipc | System V IPC、POSIX 訊息佇列 | CLONE_NEWIPC | 容器間共享記憶體 / 訊息佇列互不可見 |
| user | UID / GID 映射 | CLONE_NEWUSER | 容器內的 root 可映射成 host 上的非特權使用者 |
| cgroup | cgroup 階層的根 | CLONE_NEWCGROUP | 容器看不到 host 的 cgroup 樹結構 |
| time | boot / monotonic 時鐘偏移 | CLONE_NEWTIME | 容器可有自己的開機時間基準（kernel 5.6 加入） |

值得記住這串的歷史節奏，因為它解釋了為什麼隔離有強有弱：mnt 早在 2002 年就有了，uts/ipc 是 2006、pid 是 2008、net 大致 2009 補齊；而 **user namespace 遲至 2013（kernel 3.8）才算完成**，time namespace 更晚到 2020（kernel 5.6）。隔離能力是十幾年一塊塊長出來的，不是一次設計好的——這也是為什麼「容器內 root」這件事的安全性比你想的微妙（稍後會看到）。

把這串拼起來看一個容器啟動的瞬間：runc 呼叫 `clone()`（或先 `unshare()` 再操作），帶上一串 `CLONE_NEW*` flag，kernel 就為這個新行程一口氣開出一整組嶄新的 namespace。新行程睜開眼，看到的是一張只有它自己的 PID 表、一份它自己的掛載樹、一套它自己的網卡——一個被精心佈置好的孤島。它跑的程式完全不必知道這件事，照常 `getpid()` 拿到 1、照常綁 80 port，kernel 在背後把每一次查詢都導向那張屬於它的表。

但 namespace 只解了「看得到什麼」。一個被關進孤島的行程，視野是窄了，力氣可一點沒小——它還是能瘋狂 `malloc`、把 CPU 跑滿、把磁碟 I/O 打爆。視野的牆擋不住資源的洪水。

## cgroup：限制「能用多少」

cgroup（control group）補的正是這道缺口。如果說 namespace 是給行程戴上一副只看得到自己的眼罩，cgroup 就是給它套上一個有額度的錢包：這個群組最多用 0.5 顆 CPU、512 MiB 記憶體、多少 I/O 頻寬，超過就管制。

現代 Linux 用的是 **cgroup v2**（單一統一階層，取代了 v1 那套每種資源各一棵樹的混亂設計），到 2026 主流發行版（RHEL 9、近期 Ubuntu/Debian 等）都已預設 v2。它的介面是一棵掛在 `/sys/fs/cgroup` 下的目錄樹：每個 cgroup 是一個目錄，你把行程的 PID 寫進它的 `cgroup.procs`，再往 `memory.max`、`cpu.max` 之類的控制檔寫上限，kernel 的對應 controller 就會盯著這群行程的用量去執行那個額度。

這裡藏著一個容易被忽略、卻決定容器行為的事實：**CPU 超額和記憶體超額，kernel 的處置方式天差地別。**

CPU 是可壓縮資源。你設 `cpu.max` 把容器限在 0.5 顆 CPU，意思是每個排程週期它只分得到一半的 CPU 時間。它想用更多？沒有，kernel 就讓它**等**——行程被 throttle、變慢，但不會死。慢是可以忍受、可以恢復的狀態。

記憶體是不可壓縮資源。你給的 512 MiB 用完了，kernel 沒辦法叫一個已經寫進記憶體的 byte「等一下」——記憶體要嘛在、要嘛不在。當一個 cgroup 的記憶體用量撞上 `memory.max`、又回收不出空間，kernel 就在這個 cgroup 內觸發 **OOM killer**，挑行程殺掉。對一個典型容器來說，PID 1 就是你的主程式，於是它直接被 SIGKILL（信號 9）處決，容器當場消失。

這就是那個讓無數人半夜被叫起來的 **exit code 137** 的真相：137 = 128 + 9，主流 shell（bash／zsh／ksh）約定「被信號 N 殺死」的退出碼是 128 + N，9 是 SIGKILL（POSIX 本身只規定被信號終止的退出碼要大於 128，128 + N 這個具體編碼是 shell 的慣例）。容器沒有拋出 `OutOfMemoryError`、沒有印任何優雅的錯誤、沒留遺言——它是被 kernel 從外面一槍打死的，連反應的機會都沒有。要確認是不是 OOM 而非別人 `kill -9`，得去查容器狀態的 `OOMKilled` 旗標，或在 host 的 kernel log 裡找「memory cgroup out of memory」那行。**CPU 不足讓你的服務變慢，記憶體不足讓你的服務暴斃**——這兩種失敗模式的差別，根源就在這兩種資源一個可壓縮、一個不可壓縮。

## 一個會咬人的 worked example：盒子裡的程式以為自己有多大

把 cgroup 記憶體限制這件事手算到底，會逼出一個非常實際、也非常經典的坑。

假設你給一個容器設 `--memory=512m`，裡面跑一個 Node 服務。Node 底下的 V8 引擎為了決定「heap 長到多大要積極做 garbage collection」，需要知道「我有多少記憶體可用」。問題來了：它去問誰？

天真的 runtime 會去問 host——讀 `/proc/meminfo`，看到的是**整台機器**的記憶體，比如 32 GiB。於是它把 GC 的觸發門檻設得很高，覺得「離爆還早得很，先別急著回收」，放手讓 heap 一路長。它哪知道自己其實被關在一個 512 MiB 的盒子裡。heap 長到大約 512 MiB 那一刻，host kernel 的 cgroup memory controller 看到這個 cgroup 撞上 `memory.max`，OOM killer 出手，PID 1 應聲倒地，退出碼 137。程式從頭到尾覺得自己離記憶體上限還遠——它問錯了人。

好消息是現代 Node（12 以後，含 20、22）已經是 **container-aware** 的：它會去讀 cgroup 的記憶體上限，把 V8 的 old space 預設設成容器上限的大約一半（512 MiB 容器 → 約 256 MiB heap），所以多半不會再「以為自己有 32 GiB」。但這個坑沒消失，只是換了位置藏起來，兩個破口仍在：

其一，如果**手動**把 `--max-old-space-size` 設過大（比如照抄某篇老文章設成 1536），就等於親手覆蓋掉那份 container-aware 的保守預設，叫 V8 無視盒子有多大、一路長到撞牆。這個動作看起來像在「調效能」，實際效果卻是把那份保守預設整個蓋掉、拆掉了那張安全網。

其二，也是更隱蔽的——**heap 只是記憶體的一部分**。V8 的 old space 額度管的是 JS heap，但容器吃掉的實體記憶體（RSS）遠不只 heap：native buffer、每條執行緒的堆疊、各種 runtime 開銷、你載入的原生模組，全都算進 cgroup 的帳，卻都不在 V8 的 old space 額度裡。於是會出現一種詭異的局面：heap 用量明明守規矩、離 256 MiB 還有空間，總 RSS 卻已經悄悄逼近 512 MiB——一旦碰到，OOM killer 一樣不留情。

所以真正穩的做法有兩條：把 `--max-old-space-size` **顯式設成略低於容器上限**、預留出那塊非 heap 的開銷；以及**監控 RSS 而不是只盯 heap**。這整個坑的本質可以濃縮成一句話：**程式以為自己擁有的，跟盒子實際給的，是兩回事。** namespace 給了它「我是一台獨立機器」的錯覺，這份錯覺在記憶體計帳上會反咬一口——它以為的「整台機器」，其實是 host 的 32 GiB，而真正管它死活的，是它根本沒察覺的那個 512 MiB 的 cgroup 額度。

## 沒人造過「容器」：Docker、containerd 與 runc 的分工

到這裡該回答一個被刻意延後的問題：上面那些 `clone()`、寫 cgroup 控制檔的動作，到底是誰在做？答案是——**不是 Docker 本身**。

「Docker」在今天其實是一疊分層的工具，真正碰 kernel 的是最底下那一小塊。你下一個 `docker run`，這條命令會這樣往下傳：

```
docker CLI
    -> dockerd (Docker daemon)
         -> containerd        高階 runtime：管 image 拉取、解壓成 OCI bundle、
                              管容器生命週期
              -> containerd-shim   每個容器一個常駐的「替身父行程」
                   -> runc          低階 OCI runtime：真正 clone() 出帶
                                    namespace 的行程、掛 cgroup、套 seccomp，
                                    最後 execve 你的程式，然後 runc 自己退場
```

這條鏈每一層各管一件事，分層是有道理的：

**containerd** 是高階 runtime，負責把抽象的「我要跑這個 image」翻譯成具體準備工作——把 image 一層層拉下來、解壓成一個符合 OCI 標準的 bundle（一份根檔案系統 ＋ 一個描述「要開哪些 namespace、設多少記憶體、套什麼 seccomp」的 `config.json`），管理容器的整個生命週期。

**runc** 是低階 OCI runtime，是真正動手的那一個，但它的生命短得驚人。它讀那份 `config.json`，呼叫 `clone()` / `unshare()` 開出指定的那組 namespace，把行程寫進對應的 cgroup、套上 seccomp profile 與 capabilities 削減，最後 `execve` 啟動你的程式——然後 **runc 自己就退出了**。它的工作只是「把容器生出來並佈置好現場」，生完就走人。

那容器生出來之後，誰當它的爸爸？這就是 **containerd-shim** 存在的原因，也是這套架構裡最不直觀、卻最關鍵的一塊設計。runc 退場後，shim 成為容器行程的父行程，常駐在那。它扛起兩件事：一是回收容器退出時的 exit code、轉發 stdio；二、也是更重要的——**讓容器的命脈和 containerd / dockerd 脫鉤**。

想想看：如果容器的父行程是 dockerd，那你每次重啟或升級 dockerd，所有容器豈不是要跟著陪葬？shim 這層「替身父行程」正是為了切斷這個耦合——它替每個容器擋在前面當父行程，於是你可以重啟 dockerd、甚至升級 containerd，底下跑著的容器**毫髮無傷**，因為它們的爸爸是 shim，不是那個被你重啟的 daemon。這是「控制面可以重啟，資料面不受影響」這個分散式系統設計原則，在單機容器架構裡的一次具體落地。

這也順帶解釋了一件實務上常見的怪事：你 `docker run` 失敗，錯誤訊息卻是 `OCI runtime create failed: runc create failed`。那是因為真正執行創建的是鏈條最底端的 runc，它撞牆時的抱怨會原汁原味一路往上冒到你的終端機——你看到的是最底層工人的報錯，不是包工頭的。

順帶把另一個常被混為一談的東西分清楚：上面講的是「容器怎麼被執行起來」，而「Docker image」是完全不同的另一回事，它是容器**啟動前**的素材，下一節單獨講。

## image 是怎麼疊出來的：唯讀層、copy-on-write 與啟動的瞬間

容器跑起來那一刻看到的根目錄，不是憑空變出來的，是一疊 image layer 疊出來的幻覺，而支撐這個幻覺的是 overlay 檔案系統（現代用 overlay2）。

一個 Docker image 是**一疊唯讀的檔案系統層**外加一份 metadata。你的 Dockerfile 每一個有意義的指令——`FROM`、`COPY`、`RUN`——大致對應一層。這些層全是唯讀的、可被多個容器共享：十個容器都基於同一個 `node:20` image 跑，它們**共用**底下那幾層唯讀的 base，磁碟上只存一份。這就是容器密度高的一半祕密——啟動第十個容器，不需要再複製一份作業系統檔案。

overlay 把這疊層組裝成單一視圖的方式，是定義幾個角色：

- **lowerdir**：那疊唯讀的 image layer，疊在下面。
- **upperdir**：容器啟動時新建的一層**空的可寫層**，疊在最上面。
- **merged**：把上下所有層合併後呈現給容器的那份視圖——容器看到的根目錄，就是這個 merged。
- **workdir**：overlay 內部周轉用的一個必須是空的暫存目錄。

容器看 merged 時，上層的檔案蓋住下層的同名檔案，所以你在 image 裡放的東西它看得到，你在容器裡新建的東西也看得到，融成一份完整的根目錄。妙處在**寫**的時候。整疊 image 是唯讀的，容器要改一個來自下層的檔案怎麼辦？overlay 不會（也不能）去動唯讀的下層，它做 **copy-up**：先把那個檔案從 lowerdir 整份複製到 upperdir，然後讓容器去改那份複本。這就是 **copy-on-write**——只有在真正要寫的那一刻，才複製。沒被改過的檔案，永遠只有 image 那一份、所有容器共享。

這個機制有兩個會咬人的細節值得記住。其一，overlay 的 copy-up 是**整檔複製**、不是區塊級的：你在一個 2 GB 的檔案裡改一個 byte，overlay 會把整個 2 GB 複製到可寫層，然後才改那一個 byte。對大檔案做頻繁小修改，是 overlay 上一個安靜的效能與空間陷阱。其二，刪除下層的檔案也不能真刪——overlay 改在上層放一個叫 **whiteout** 的特殊標記檔，告訴 merged 視圖「這個檔案要當作不存在」。下層那份檔案其實還躺在那、還佔著空間，只是被遮住了。

現在把整個啟動瞬間連起來重放一遍：containerd 把 image 各層解壓好當 lowerdir，新建一層空的 upperdir，用 overlay mount 成 merged，把這份 merged 當作容器的根檔案系統寫進 OCI bundle；runc 接手，`clone()` 出帶整組 namespace 的行程、掛上 cgroup、套上 seccomp，把那份 merged 透過 mnt namespace 變成這個行程眼中的 `/`，最後 `execve` 啟動你的程式。從此這個行程活在一個有自己的根目錄、自己的 PID 表、自己的網卡、有記憶體額度上限的孤島裡——而它跑的程式對這一切一無所知，只覺得自己開機在一台乾淨的新機器上。

這裡也順手解了一個常見的坑：**容器是 ephemeral 的，那層可寫的 upperdir 隨容器銷毀而消失。** 你以為寫進去的資料，容器一刪就跟 upperdir 一起蒸發了。狀態必須寫進 volume 或外部儲存，別寫進容器自己的可寫層——它從設計上就是用完即棄的。

## 「能做什麼」這一層：root 其實不一定是 root

namespace 管視野、cgroup 管額度，還剩最後一道問題：就算一個容器看不到別人、用量也被掐住，它**對 kernel 能發起什麼動作**？因為所有容器共用同一顆 kernel，一個容器若能呼叫某個危險的 syscall 去戳 kernel 的軟肋，視野和額度的牆都擋不住它。這一層由三樣東西把守。

**capabilities** 把傳統 Unix「root 全能 / 非 root 幾乎無能」的二分法，切成四十幾個獨立的小權限：綁低號 port 是一個 capability、改系統時間是一個、載入 kernel 模組是一個。容器執行時預設只給一小撮、砍掉其餘大部分，於是即使容器內是 root，它能幹的危險事也被大幅縮編。

**seccomp** 則直接在 syscall 這一層築牆。runc 預設會給容器套一份 seccomp profile，**這份預設 profile 從三百多個 syscall 裡封掉大約 44 個**（依 Docker 官方說法，2026-06）。被封的都是明顯危險、正常應用根本用不到的——像直接操作 kernel 模組、改 host 時鐘那類。但要看清這個數字的另一面：封 44 個，意思是**剩下兩百多個是放行的**。預設 seccomp 擋掉的是「明顯的兇器」，遠不是最小權限。它降低了攻擊面，但別把它當成一道密不透風的牆。

最微妙、也最該講透的是 **user namespace**，因為它直接戳破一個幾乎人人都有的錯覺：**容器裡的 root，不一定是 host 上的 root。**

預設情況下（沒開 user namespace 時），容器裡的 UID 0 **就是** host 的 UID 0。容器裡那個 root 和 host 上那個 root，是同一個 UID。這意味著什麼？意味著一旦有人從容器逃逸出來——透過某個 kernel 漏洞、或某個被你寬鬆掛載進去的 host 路徑——他拿到的是 **host 上貨真價實的 root**。容器那層「我是這台機器的 root」的威風，逃逸的瞬間就成了 host 上真正的最高權限。

user namespace 就是來拆這顆炸彈的。它在容器的 UID 和 host 的 UID 之間架一張映射表：容器裡的 UID 0（root），映射到 host 上一個**高號、完全沒有特權**的 UID，比如 100000 或 231072。映射靠 `/etc/subuid` 和 `/etc/subgid` 兩個檔定義一段 UID 區間。效果是：容器內那個行程在自己的 user namespace 裡是威風凜凜的 root、UID 0，可以對它自己那塊天地為所欲為；可一旦它試圖對 host 動手，kernel 看到的是一個 UID 100000 的無名小卒——這個號碼在 host 上**根本不對應任何真實使用者**，更別說 root。它在牆內是國王，翻牆出去就成了黑戶。逃逸後能造成的破壞，被這層映射狠狠地縮小了爆炸半徑。

把這三層連起來看，「容器是個安全沙箱」這句話就有了精確的邊界：capabilities 削減了 root 的權柄、seccomp 封掉了一批兇器、user namespace 讓容器 root 在 host 上一文不值——這幾道牆疊起來確實擋掉了一大片攻擊面。但它們有一個共同的、無法繞過的前提，下一節就講這個前提，以及它在哪裡會整個崩掉。

## 那道擋不住的縫：共用 kernel 這個前提

回到全章的起點：容器底下沒有一份額外的 kernel，所有容器和 host **共用同一顆 host kernel**。namespace、cgroup、seccomp——這些隔離全是這顆 kernel 自己提供、自己執行的功能。這帶來容器最致命的一道結構性侷限：

**容器之間、容器與 host 之間的隔離邊界，就是那顆共用 kernel 的攻擊面。** 只要 host kernel 本身有一個可被利用的漏洞，一個惡意容器就有機會穿過所有 namespace 的牆，直接逃逸到 host 或鄰居容器。對比之下，VM 各跑一份自己的 guest kernel，要逃逸得先打穿 guest kernel、再打穿 hypervisor，多了一道貨真價實的硬牆。**容器的隔離強度，先天就低於 VM**——這不是 Docker 實作得好不好的問題，是「共用 kernel」這個選擇的內在代價。你拿啟動速度和密度，換掉了一層隔離。

這道理一推開，幾個實務上的紅線就都站住了腳：

`--privileged` 為什麼是核武級的危險——它幾乎拆光上面講的所有牆：給回全部 capabilities、放開 device 存取、關掉多數限制，等於把容器和 host 之間那層薄薄的隔離整個掀掉。debug 時順手加、然後忘了拿掉，等於讓那個容器在 host 上常態裸奔。

為什麼多租戶跑**不信任的程式碼**時，光靠容器不夠——當你要在同一台機器上跑一堆來自互不信任的人的程式碼，共用 kernel 的攻擊面就成了真實的威脅，一個被精心構造的惡意容器可能打穿 kernel 漏洞逃逸。這種場景下，業界的做法是在容器外再包一層補強隔離：用 gVisor 那樣在容器與 host kernel 之間插一個攔截、過濾 syscall 的中介層，或用 Kata Containers 那樣讓每個容器跑在一個極輕量的專屬 VM 裡——本質都是把那顆「共用 kernel」重新切開，把硬牆補回來，代價是吃回一些啟動開銷與相容性。

也為什麼「容器能跑不同 OS」是個誤解——容器共用 host kernel，所以 Linux 容器需要的是 **Linux kernel**。你在 macOS 或 Windows 的 Docker Desktop 上跑 Linux 容器，看似在原生跑，其實 Docker Desktop 偷偷起了一個 Linux VM，你的容器是跑在那個 VM 的 Linux kernel 上的。沒有「共用」到一顆對的 kernel，容器根本無從談起。

## 為什麼是這個形狀

退一步看，容器的整個樣貌，都是從一個取捨裡長出來的：**它選擇共用 host kernel，用一層隔離去換啟動速度與密度。**

正因為共用 kernel，它才不需要為每個工作負載開機一份新 kernel——所以它能毫秒級啟動、能在一台機器上塞下幾百個。正因為沒有物理屏障可用，它只能靠改變每個行程「看到什麼（namespace）、能用多少（cgroup）、能做什麼（capabilities / seccomp / user namespace）」來造出隔離的錯覺。也正因為這層隔離全建立在那顆共用 kernel 上，它的安全邊界先天就比 VM 軟——kernel 一旦破，牆就全倒。

所以容器不是「更輕的 VM」，它是另一種東西：一群被 kernel 原語精心框住的普通行程，用一場製作精良的錯覺，換來了密度與速度，同時誠實地保留著「我們其實共用一顆心臟」這個事實。理解了這一點，你看 `docker run` 就不再是一個黑盒指令，而是一連串具體的動作——開 namespace、掛 cgroup、疊 overlay、套 seccomp、`execve`——以及這每一個動作各自買到了什麼、又各自留下了哪一道擋不住的縫。

## 延伸閱讀

- [namespaces(7) — Linux manual page（八種 namespace 的權威總覽）](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [cgroups(7) — Linux manual page](https://man7.org/linux/man-pages/man7/cgroups.7.html)
- [Control Group v2 — The Linux Kernel documentation（cgroup v2 統一階層與 memory.max / OOM 行為）](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [Open Container Initiative — Runtime Specification（OCI runtime spec，runc 遵循的標準）](https://github.com/opencontainers/runtime-spec)
- [Docker — Seccomp security profiles（官方，含「預設封掉約 44 個 syscall」）](https://docs.docker.com/engine/security/seccomp/)
- [Docker — Isolate containers with a user namespace（容器 root 到 host UID 的映射）](https://docs.docker.com/engine/security/userns-remap/)
- [Docker — OverlayFS storage driver（lowerdir / upperdir / copy-up / whiteout 的官方說明）](https://docs.docker.com/engine/storage/drivers/overlayfs-driver/)
