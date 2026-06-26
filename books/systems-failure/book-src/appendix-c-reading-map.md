# 附錄 C — 經典書單與調查報告地圖

這份地圖分兩層：先是奠定整個領域的經典著作（本書的眼鏡從這裡磨出來），再是本書每一個案例的一手調查報告與其連結。前者教你「怎麼看」，後者讓你「自己去看」——任何一場災難，最該讀的永遠是它的官方調查報告原文，而不是二手的「某某人犯了錯」標題。連結以本書 landscape 查證過者為準；少數未在 landscape 釘死特定 URL 者標「（未驗證）」。

---

## 第一層：領域經典

這些是反覆出現在全書故障解剖與失敗模式語言（F1–F14）背後的源頭。每一條都值得在你寫下一份 postmortem 之前讀過。

- **Charles Perrow,《Normal Accidents: Living with High-Risk Technologies》(1984)**——本書一號主張的源頭，也是書名的出處。「互動複雜度 × 緊耦合」的二維分類、以三哩島為原型發展出的「嚴重事故是系統的正常產物」概念都出自這裡。讀它你會永遠改變對「高風險系統」的直覺。**支撐 ch01（理論定調）、ch16（三哩島正是它的原型案例）。**

- **James Reason,《Human Error》(1990)**——「瑞士起司模型」的原典，以及 latent condition（潛伏條件）vs active failure（觸發）的區分。F3、F8 的理論底座，也是航空、醫療、核能安全文化的共同地基。讀它學會「別只看最後犯錯的那隻手，要看整排早就破掉的起司」。**支撐 ch01（瑞士起司首次出場）、ch02（潛伏 vs 觸發的方法）。**

- **Richard I. Cook,〈How Complex Systems Fail〉(1998，十八條)**——幾頁長、終身受用。「複雜系統永遠運行在退化模式」「災難需要多重失效合謀」「根因是事後建構」這幾條全書一再回收，都在這篇。建議印出來貼在你寫 postmortem 的地方。**支撐 ch01、ch02（方法論章的源頭）。** 全文：<https://how.complexsystems.fail/>

- **Sidney Dekker,《Drift into Failure》**——「漂移到失效」「局部理性」「遞減主義」的出處：系統如何在一連串各自合理的小步子裡走向災難。讀完你會用不同的眼光看自己 backlog 裡那些「以前都這樣」。**支撐 ch02（定義漂移）、ch14（漂移主打）、ch22（韌性是設計、不是運氣的理論底座）。**

- **Sidney Dekker,《The Field Guide to Understanding Human Error》**——「舊觀點 vs 新觀點」「人為疏失是症狀不是原因」「替代故事」的完整論證；後半教你怎麼用高解析度時間線（含「當下掌握的資訊」欄）寫一份不被後見之明汙染的調查。**支撐 ch02（讀事故報告的方法）。**

- **Sidney Dekker,《Just Culture: Balancing Safety and Accountability》**——把「blameless 為什麼是工程必要」講透，並誠實處理「那魯莽與蓄意破壞怎麼辦」這條最難的界線。**支撐 ch02（just culture 為何是工程必要）。**

- **Diane Vaughan,《The Challenger Launch Decision: Risky Technology, Culture, and Deviance at NASA》(1996)**——「偏差正常化」（normalization of deviance）一詞的學術源頭與最完整論證。一本社會學家的厚書，但「危險訊號如何被一次次重新定義為可接受」這個機制，值得每個寫 SRE 的人懂。**支撐 ch02（預告）、ch14（挑戰者）、ch15（哥倫比亞，同一機制的復發）。**

- **Nancy G. Leveson,《Engineering a Safer World: Systems Thinking Applied to Safety》(2012)**——把安全當成系統控制問題（STAMP/STPA），主張事故是「控制結構失靈」而非「零件鏈式失效」；與 Perrow 互補，給出可操作的工程方法。Leveson 也是經典醫療輻射治療機事故分析的作者，整本書是「為什麼要把安全設計進系統、而不是事後追究個人」的集大成。**呼應全書「系統而非個人」的核心立場，方法論延伸閱讀。** （未驗證）

- **Lisanne Bainbridge,〈Ironies of Automation〉,《Automatica》(1983)**——F5「自動化的諷刺」的原典。1983 年就精確預言了法航 447 的形狀：你越自動化常規操作，就越剝奪操作員應付異常的練習與狀況意識，於是最需要人接手時，人最沒準備。短、深、必讀。**支撐 ch05（法航 447）、ch06（于伯林根）。**

---

## 第二層：各案一手調查報告

依本書章節順序排列。每一條優先列官方/一手調查報告與其連結，附一句「讀它為了看什麼」。

### ch03 — 塔科馬海峽橋（1940）／凱悅麗晶走道（1981）

- **K. Yusuf Billah & Robert H. Scanlan,〈Resonance, Tacoma Narrows Bridge Failure, and Undergraduate Physics Textbooks〉,《American Journal of Physics》59(2), 1991**——本書最重要的一條校正：明確駁斥「共振版」、釘正為 aeroelastic flutter（自激顫振）。讀它為了看「全世界（含教科書）一起記錯一件事」是怎麼回事——這正是本書的可信度來源。AJP：<https://pubs.aip.org/aapt/ajp/article/59/2/118/532864> ；摘要鏡像：<https://www.vibrationdata.com/Tacoma.htm>
- **NBS（今 NIST）,《Investigation of the Kansas City Hyatt Regency Walkways Collapse》, NBSIR 82-2465, 1982**——凱悅的一手官方調查。讀它為了看「技術直接因（連接載重加倍）＋組織根因（沒有人重算那個變更）要一起寫進結論」。<https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir82-2465.pdf>
- **Hyatt Regency 工程倫理案例（Online Ethics Center）**——焦點在「記錄工程師的責任邊界」與「那通有爭議的核准電話」。讀它為了照見你 code review 流程裡「大家都以為別人會檢查」的鏡子（史實細節仍以 NBS 報告為準）。<https://onlineethics.org/cases/hyatt-regency-walkway-collapse>

### ch04 — 波音 737 MAX / MCAS（2018、2019）

- **印尼 KNKT/NTSC,《Lion Air JT610 最終報告》(2019-10)**——一手調查報告，列出九項 contributing factors。讀它的 contributing factors 清單，對照本章的起司孔洞表，看「多重失效合謀、非單一根因」的範本。<http://knkt.go.id/Repo/Files/Laporan/Penerbangan/2018/2018%20-%20035%20-%20PK-LQP%20Final%20Report.pdf>
- **美國眾議院運輸委員會,《737 MAX 調查最終報告》(2020-09)**——組織線的權威來源。讀它為了看 ODA 自我取證制度的失靈如何形成「失靈的取證制度」這層孔洞。<https://transportation.house.gov/imo/media/doc/2020.09.15%20FINAL%20737%20MAX%20Report%20for%20Public%20Release.pdf>
- **FAA,《737 MAX Return to Service 摘要》**——監管方視角的復飛條件。讀它為了看 MCAS 最終被改成什麼樣（雙 AoA 比對、分歧停用）——「該怎麼設計才對」的官方版答案。<https://www.faa.gov/sites/faa.gov/files/2022-08/737_RTS_Summary.pdf>

### ch05 — 法航 447（2009）

- **BEA（法國航空事故調查局）,《Final Report on the accident on 1st June 2009 to the Airbus A330-203 registered F-GZCP operated by Air France flight AF447》(2012-07-05)**——一手權威。讀它為了看調查報告本身對「自動化交接、失速警告邏輯、訓練」的批評，而不是二手的「飛行員失誤」標題。<https://bea.aero/en/investigation-reports/notified-events/detail/accident-to-the-airbus-a330-203-registered-f-gzcp-and-operated-by-air-france-on-01-06-2009/>
- **William Langewiesche,〈The Human Factor〉,《Vanity Fair》(2014)**——對 AF447 駕駛艙人因與 Airbus 飛控哲學最好的長篇敘事之一，把「自動化如何重塑並侵蝕飛行員技能」寫得克制而透徹。（背景敘事，非調查報告）

### ch06 — 于伯林根空中相撞（2002）

- **BFU（德國聯邦航空事故調查局）,《Investigation Report AX001-1-2/02》(2004-05)**——一手調查報告。讀它如何**拒絕**把主因歸到機組，而是並列「Skyguide 系統性缺失」與「TCAS-vs-ATC 優先權模糊」兩條主因，提出 19 項建議。SKYbrary 條目：<https://skybrary.aero/bookshelf/bfu-investigation-report-ax001-1-202-uberlingen-mid-air> ；報告全文 PDF（Glasgow 鏡像）：<https://www.dcs.gla.ac.uk/~johnson/Eurocontrol/Ueberlingen/Ueberlingen_Final_Report.PDF>
- **ICAO 對 TCAS/ACAS 程序的修訂（2003-11 起，RA 優先於 ATC）**——讀它為了看一條「明確優先權規則」如何從一場災難中淬煉出來、成為全球標準（可由 ICAO Annex 與 PANS-OPS 中關於 ACAS RA 的條文查證）。（未驗證：無單一固定 URL）

### ch07 — 金姆利滑翔機（1983）

- **加拿大 Board of Inquiry（Justice George Lockhart 主持，1985）的調查結論**——這場事件的官方一手判斷。讀它為了看它**如何拒絕「歸咎個人」、把主責指向企業與設備層面缺失**，並建議全面改用 SI 公制——一份三十多年前就示範了 just culture（見 ch02）的報告。（未驗證：無穩定線上全文 URL，內容經多源轉述）
- **CBC,〈metric mix-up led to Gimli Glider emergency〉**——把「剛改公制的機隊」這個制度性的縫講清楚，適合對照你自己團隊「剛遷移到新系統、舊習慣還沒改」的危險期。<https://www.cbc.ca/news/canada/manitoba/gimli-glider-35-years-1.4756985>

### ch08 — Schiaparelli 火星著陸器（2016）

- **ESA ExoMars 2016 — Schiaparelli Anomaly Inquiry（SIB 報告，2017）**——一手調查報告，把「IMU 飽和→積分→姿態誤差→負高度→提前釋傘」的完整鏈條與四條根因講得清清楚楚，並明確建議補上高度合理性檢查。本案所有技術細節的權威來源。<https://sci.esa.int/documents/33431/35950/1567260317467-ESA_ExoMars_2016_Schiaparelli_Anomaly_Inquiry.pdf>
- **ESA 官方新聞〈Schiaparelli landing investigation completed〉**——調查完成的官方摘要，適合先讀這篇建立全貌再啃報告。<https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/Exploration/ExoMars/Schiaparelli_landing_investigation_completed>

### ch09 — Sleipner A 平台（1991）

- **SINTEF 技術調查（Statoil 委託）**——一手技術調查的權威來源。結論把根因明確定在「NASTRAN 有限元素分析對 tricell 牆剪應力低估約 47%＋偏不保守的混凝土設計」，而非材料或施工。讀它為了看「模型誤差如何凝固成結構缺陷」。（未驗證：無穩定線上全文 URL，由參與者著作與後續論文轉述）
- **Douglas N. Arnold,〈The sinking of the Sleipner A offshore platform〉（明尼蘇達大學數學系教案）**——一位數值分析學者把這場災難寫成有限元素法的經典反例。讀它如何用加密網格重現破裂深度，理解「離散化即假設」、網格細緻度不是精度微調而是「對不對」的問題。<https://www-users.cse.umn.edu/~arnold/disasters/sleipner.html>
- **Equinor / Norsk industriminne,〈Sleipner A GBS – lost and replaced〉**——業主方的事件敘事與後續重建，含「人員安全撤離」與 NOK 計損失口徑，適合校對規模與時序細節（財務損失各源口徑不一，見本章 ⚠️）。<https://equinor.industriminne.no/en/sleipner-a-gbs-lost-and-replaced/>

### ch10 — Cloudflare 的一條 regex（2019）

- **Cloudflare 官方 postmortem**：John Graham-Cumming,《Details of the Cloudflare outage on July 2, 2019》(2019-07-12)——一手來源，罕見地誠實：逐項列出 regex 原文、`x=x` 23 步／5,353 步的實測、Quicksilver 跳過分階段發布、CPU 護欄被誤刪。一篇教科書級的 blameless postmortem，值得當範本讀。<https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/>
- **Russ Cox,《Regular Expression Matching Can Be Simple And Fast》**——讀它為了懂回溯引擎為什麼會指數爆炸、RE2 為什麼選擇線性時間，也就懂 Cloudflare 為什麼「用對引擎就不會出事」。<https://swtch.com/~rsc/regexp/regexp1.html>
- **OWASP ReDoS**——把這場「自己打自己」的事故，連到「攻擊者能不能故意餵這種輸入打你」的安全視角。<https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS>

### ch11 — 2010 閃電崩盤

- **U.S. CFTC & SEC,《Findings Regarding the Market Events of May 6, 2010》(2010-09-30)**——一手聯合調查報告，本案事實的錨。最值得讀的是它**沒做的事**：從頭到尾用市場結構與自動化互動解釋崩盤、不點名任何單一兇手——這份報告本身就是「找單一根因是錯的問法」（見 ch02）的範本。「燙手山芋」與「9% 成交量參與率、無價格／時間限制」都出自此處。<https://www.sec.gov/files/marketevents-report.pdf>
- **Kirilenko, Kyle, Samadi & Tuzun,《The Flash Crash: High-Frequency Trading in an Electronic Market》(The Journal of Finance, 2017)**——用 E-mini 逐筆稽核資料的學術分析，呼應官方報告：HFT 沒引發崩盤、但透過搶先要求即時成交而加劇它，並支持「即使沒有 Sarao 也可能發生」。讀它理解為什麼歸因到單一交易者是過度簡化。<https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1686004>
- **SEC, Investor Bulletin: Measures to Address Market Volatility（單股熔斷與 Limit Up-Limit Down）**——事後補上那道煞車的官方說明。讀它把「市場的 circuit breaker／rate limit」和你後端的熔斷與限速對照起來。<https://www.sec.gov/oiea/investor-alerts-bulletins/investor-alerts-circuitbreakersbulletinhtm.html>

### ch12 — 德州電網 2021

- **FERC／NERC 聯合報告**：《The February 2021 Cold Weather Outages in Texas and the South Central United States》(2021-11)——一手來源，本章事實錨，含 28 項正式建議。讀它如何用數據（18,000 MW 天然氣停機、燃料問題佔比、防寒未強制）反駁「天災／單一能源」迷思，本身就是一堂「怎麼讀事故報告」的課。<https://www.ferc.gov/news-events/news/final-report-february-2021-freeze-underscores-winterization-recommendations>
- **2011 年 FERC／NERC 報告**：《Report on Outages and Curtailments During the Southwest Cold Weather Event of February 1–5, 2011》——十年前的那份報告。把它和 2021 的並排讀，你會親眼看到「同樣的建議寫了兩次、中間沒被強制執行」——偏差正常化的鐵證，也是哥倫比亞（見 ch15）「action items 會腐爛」的基礎設施版。（未驗證：無單一固定 URL，由 FERC/NERC 文庫提供）
- **〈2021 Texas power crisis〉(Wikipedia)**——整合了死亡人數的官方統計（約 210–246）與研究估計（約 700）、經濟損失範圍、孤島電網的歷史脈絡。當作交叉查證與 hedge 的起點，硬數字仍以 FERC/NERC 報告為準。<https://en.wikipedia.org/wiki/2021_Texas_power_crisis>

### ch13 — 雲端連鎖（CrowdStrike 2024、AWS S3 2017、Fastly 2021、Meta BGP 2021）

- **CrowdStrike 官方 RCA**：《Channel File 291 Incident — External Technical Root Cause Analysis》(2024-08-06)——本章主案一手來源。逐項講清 21 對 20 欄位、越界讀取、Content Validator 缺陷、「Rapid Response Content 無分階段發布」這條核心孔洞。把「內容更新」當「程式碼」對待，值得每個會推設定到全球的人讀。<https://www.crowdstrike.com/wp-content/uploads/2024/08/Channel-File-291-Incident-Root-Cause-Analysis-08.06.2024.pdf>
- **AWS S3 us-east-1 postmortem**：《Summary of the Amazon S3 Service Disruption in the Northern Virginia (US-EAST-1) Region》——一手來源。讀「狀態頁本身依賴 S3 所以無法顯示故障」那段，它是「隱藏相依／監控與被監控共命運」最簡潔的真實案例。<https://aws.amazon.com/message/41926/>
- **Fastly 官方 postmortem**：Nick Rockwell,《Summary of June 8 outage》——一手來源，且坦白。「5/12 引入潛伏 bug、6/8 一筆合法設定觸發」是「潛伏條件 vs 觸發」的教科書。<https://www.fastly.com/blog/summary-of-june-8-outage>
- **Meta BGP 事故說明**：《More details about the October 4 outage》(Engineering at Meta, 2021-10-05)——一手來源。看「DNS 自動撤回 BGP 把局部放大成全球」與「修復工具／門禁依賴已斷網路」兩段——後者是「復原路徑的循環依賴」最痛的示範。<https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/>

### ch14 — 挑戰者號（1986）

- **《Report of the Presidential Commission on the Space Shuttle Challenger Accident》(Rogers Commission, 1986-06)**——一手官方調查報告。一定要讀它如何把結論分成「物理因（O-ring）」與「貢獻因（決策過程與安全文化）」兩層——它本身就示範了拒絕單一根因的調查該長什麼樣。<https://history.nasa.gov/rogersrep/genindex.htm>
- **Richard Feynman,《Appendix F: Personal Observations on the Reliability of the Shuttle》**——Feynman 為報告寫的個人附錄，獨立成篇。讀那個 1/100,000 vs 1/100~1/200 的數量級落差，以及收尾那句「reality must take precedence over public relations, for nature cannot be fooled」——整個 Part V 的座右銘。<https://www.nasa.gov/history/rogersrep/v2appf.htm> ；Caltech PDF：<https://calteches.library.caltech.edu/3570/1/Feynman.pdf>
- **Diane Vaughan,《The Challenger Launch Decision》(1996)**——「偏差正常化」的出處與最完整論證（亦見第一層）。如果你只想帶走一個概念進你的工作，就是這個。

### ch15 — 哥倫比亞號（2003）

- **《Columbia Accident Investigation Board (CAIB) Report, Volume I》(2003-08-26)**——一手調查報告。務必讀第 6 章（泡棉脫落被正常化的歷史）與第 8 章「History as Cause」（把哥倫比亞與挑戰者並排比對，本章核心論點的來源）。<https://www.nasa.gov/wp-content/uploads/2023/03/caib-report-volume1.pdf>
- **CAIB 第 8 章「History as Cause」節錄（多所大學工程倫理課採用）**——只讀一段就讀這章開頭那句「unfortunate similarities between the agency's performance and safety practices in both periods」，本章標題的出處。<https://www.montana.edu/rmaher/engr125/CAIB-History%20as%20a%20cause.pdf>
- **NASA APPEL 案例研究《Silence and Breakdown of Communication》(Rodney Rocha 案)**——從工程師視角看「異議如何在組織裡被消音」，補足調查報告較少著墨的人因細節。<https://appel.nasa.gov/wp-content/uploads/2013/04/553084main_Case_Study_Silence_Breakdown_Columbia_Rocha.pdf>

### ch16 — 三哩島（1979）

- **《Report of the President's Commission on the Accident at Three Mile Island》(Kemeny Commission, 1979-10)**——一手調查報告。讀它如何把嚴重化的根因從「設備」明確轉向人機介面、訓練與組織態度；那句「需要組織、程序、實務，尤其是態度上的根本改變」是整份報告的靈魂。NRC 館藏：<https://www.nrc.gov/reading-rm/doc-collections/news/2019/19-016.pdf>
- **NRC, Backgrounder on the Three Mile Island Accident**——官方事故概述與時間軸，適合快速校對細節。<https://www.nrc.gov/reading-rm/doc-collections/fact-sheets/3mile-isle>
- **Charles Perrow,《Normal Accidents》(1984)**——三哩島是這本書的原型案例（亦見第一層）。讀第一章如何從這場事故提煉出「互動複雜度 × 緊耦合」的二維分類。

### ch17 — 車諾比（1986）

- **IAEA, INSAG-7,《The Chernobyl Accident: Updating of INSAG-1》(1992)**——本案史實的一手錨點，也是那次關鍵翻案的原始文件：把根因從「操作員違規」改為「反應爐設計缺陷（正空泡係數、控制棒正向 scram）與安全文化缺失為首要」。讀它你會明白「人為疏失」作為調查終點有多危險。<https://www-pub.iaea.org/MTCD/publications/PDF/Pub913e_web.pdf>
- **World Nuclear Association,《Sequence of Events – Chernobyl Accident Appendix 1》**——把那晚從 01:03 到 01:23:43 的每一步逐分鐘列出，拿來對著本章時序圖重走一遍。<https://world-nuclear.org/information-library/appendices/chernobyl-accident-appendix-1-sequence-of-events>
- **World Nuclear Association,《RBMK Reactors》附錄**——把正空泡係數與控制棒正向 scram 的物理講清楚，並說明事故後 RBMK 如何被改造消除這些缺陷——印證「這從來是可修的設計問題，不是不可靠的人性」。<https://world-nuclear.org/information-library/safety-and-security/safety-of-plants/chernobyl-accident>

### ch18 — Morris 蠕蟲（1988）

- **Eugene H. Spafford,〈The Internet Worm Program: An Analysis〉(Purdue Tech Report CSD-TR-823, 1988)**——最權威的逐段剖析，確認蠕蟲不含破壞性 payload、災難來自重複感染。要看「七分之一」重感染率與行程爆量的第一手分析就讀這篇。<https://spaf.cerias.purdue.edu/tech-reps/823.pdf>
- **Mark Eichin & Jon Rochlis,〈With Microscope and Tweezers: An Analysis of the Internet Virus of November 1988〉(MIT, 1989)**——從 MIT 角度的逆向分析與當夜止血紀實，與 Spafford 互補。<https://dl.acm.org/doi/10.1145/63526.63528>
- **United States v. Morris, 928 F.2d 504 (2d Cir. 1991)**——CFAA 首例定罪的上訴判決全文，看法律體系第一次嘗試定義「未授權存取」的邊界。（未驗證：判決全文散見各法律資料庫）
- **FBI,〈The Morris Worm — 30 Years Since the First Major Attack on the Internet〉(2018)**——事件當晚氛圍與後續影響的可讀概覽。<https://www.fbi.gov/news/stories/morris-worm-30-years-since-first-major-attack-on-internet-110218>

### ch19 — Heartbleed（2014）

- **heartbleed.com（Codenomicon）**——當年為這個 bug 取名、做 logo 的網站，至今仍是最清楚的一手科普：用非技術語言講清楚洩了什麼、為什麼嚴重、該做什麼。本章「為什麼要輪換金鑰」的權威來源。<https://heartbleed.com/>
- **NVD — CVE-2014-0160**——官方漏洞條目，列出受影響版本（OpenSSL 1.0.1–1.0.1f）、CVSS 評分與技術摘要。查證版本範圍與時間線的基準。<https://nvd.nist.gov/vuln/detail/CVE-2014-0160>
- **OpenSSL 安全公告（2014-04-07）**——OpenSSL 專案自己的揭露公告，點明修補版本 1.0.1g 與緩解建議。一手來源。<https://www.openssl.org/news/secadv/20140407.txt>
- **CNN Business,〈Your Internet security relies on a few volunteers〉(2014-04-18)**——把「約四人、一名全職、年捐約兩千美元」這個組織面教訓講給大眾聽的代表性報導，理解本章「公地悲劇」孔洞的好入口。<https://money.cnn.com/2014/04/18/technology/security/heartbleed-volunteers/index.html>

### ch20 — 供應鏈即災難（SolarWinds/SUNBURST 2020、Log4Shell 2021）

- **CISA 緊急指令 ED 21-01**：《Mitigate SolarWinds Orion Code Compromise》(2020-12-13)——一手官方應變文件，讓你看到國家級事件應變的第一反應是「立刻把它斷網下線」，以及為什麼。<https://www.cisa.gov/news-events/directives/ed-21-01-mitigate-solarwinds-orion-code-compromise>
- **Mandiant/FireEye 技術分析**：《Highly Evasive Attacker Leverages SolarWinds Supply Chain Compromises with SUNBURST Backdoor》——揭露者本人的拆解，看 SUNBURST 怎麼潛伏、避沙箱、擬態 C2，理解「為什麼自動偵測抓不到」。<https://cloud.google.com/blog/topics/threat-intelligence/evasive-attacker-leverages-solarwinds-supply-chain-compromises-with-sunburst-backdoor>
- **CrowdStrike SUNSPOT 分析**：《SUNSPOT: An Implant in the Build Process》——專講編譯期注入的那把工具，本章「後門不在程式裡、在做出程式的那台機器裡」這句話的技術出處。<https://www.crowdstrike.com/en-us/blog/sunspot-malware-technical-analysis/>
- **CSRB Log4j 報告**：Cyber Safety Review Board,《Review of the December 2021 Log4j Event》(2022-07)——美國官方對 Log4Shell 的權威覆盤，「endemic」這個讓人不安的結論與 SBOM 治理缺口的呼籲都出自這裡。<https://www.cisa.gov/resources-tools/resources/cyber-safety-review-board-csrb-report-log4j>
- **NVD CVE-2021-44228**——Log4Shell 的權威漏洞紀錄，CVSS 10.0 的官方評分與受影響版本範圍（2.0-beta9 至 2.14.1）。<https://nvd.nist.gov/vuln/detail/CVE-2021-44228>

### ch21 — 溫哥華證券交易所指數截斷誤差（1982–1983）

本案沒有政府事故調查報告（它不是死人的安全事故），最權威的整理出自數值計算的學術討論，而非調查局。

- **Technical University of Munich（Huckle）案例頁**：*The Vancouver Stock Exchange*——數值計算課程整理的權威技術整理，把「truncation vs rounding、一天約 2,800–3,000 次重算、22 個月累積到真值一半」講得最清楚，並列出原始來源。讀它為了看「單向 round-off 誤差在高頻重算下線性累積、而監控結構上看不見」這條教訓的完整算術。<https://www5.in.tum.de/~huckle/Vancouv.pdf>
- **B. D. McCullough 等對數值正確性的討論**——學術文獻常引 VSE 作為「軟體數值誤差能造成重大實務後果」的標準案例（如 McCullough & Vinod 對統計／財務軟體數值可靠性的系列討論）。讀它為了把「數值正確性值得被當成一等公民去驗證」這條譜系追回源頭。（未驗證：散見多篇論文，無單一固定 URL）

### ch22 — 韌性工程／阿波羅 11（1969，正面反例）

- **NASA Apollo 11 Lunar Surface Journal — Program Alarms 專頁**——含 Bales、Garman、Hamilton 的第一手回憶與技術說明，是 1201/1202 事件的一級史料。要看「過載被優雅化解」的原始現場，從這裡開始。<https://www.hq.nasa.gov/alsj/a11/a11.1201-pa.html>
- **Don Eyles,〈Tales from the Lunar Module Guidance Computer〉(2004, AAS Guidance & Control Conference)**——寫下降導引軟體的人親自解釋 cycle steal、restart protection 與優先權排程怎麼救了登月。工程師對工程師的第一手敘述。<https://klabs.org/history/apollo_11_alarms/eyles_2004/eyles_2004.htm>
- **David A. Mindell,《Digital Apollo: Human and Machine in Spaceflight》(MIT Press, 2008)**——把阿波羅飛控放進「人與自動化如何分工」的脈絡——正好是法航 447（見 ch05）與于伯林根（見 ch06）那條自動化諷刺線的正面對照。
- **ESA Schiaparelli Anomaly Inquiry Board 報告（2017）**——本章的反面對照組一級報告。把它與阿波羅 ALSJ 並讀，就是「同樣異常、兩種設計哲學、兩種結局」最乾淨的一課。<https://sci.esa.int/documents/33431/35950/1567260317467-ESA_ExoMars_2016_Schiaparelli_Anomaly_Inquiry.pdf>

### 跨案參考：RISKS Digest

- **ACM Risks Digest（comp.risks）**——Peter Neumann 主持、運行數十年的「電腦相關風險」公共記事本，是許多早期軟體事故的當代第一手討論存檔。把它當成「失敗模式的活檔案」：本書許多案例在事發當週就在這裡被工程師逐字解剖。<https://catless.ncl.ac.uk/Risks/>
