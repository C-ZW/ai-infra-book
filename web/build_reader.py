#!/usr/bin/env python3
"""把 book/ 打包成單一離線閱讀器 web/index.html。

用法：python3 web/build_reader.py
書籍內容更新後重跑一次即可。無任何外部相依（marked.js 已 vendor 在 web/vendor/）。
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "book"
VENDOR = Path(__file__).resolve().parent / "vendor" / "marked.min.js"
OUT = Path(__file__).resolve().parent / "index.html"

GROUPS = [
    ("開始", [BOOK / "README.md"]),
    ("Part I — 心智模型與基礎", sorted((BOOK / "part-1-foundations").glob("ch*.md"))),
    ("Part II — 推論引擎", sorted((BOOK / "part-2-inference-engine").glob("ch*.md"))),
    ("Part III — 分散式推論", sorted((BOOK / "part-3-distributed").glob("ch*.md"))),
    ("Part IV — 平台工程", sorted((BOOK / "part-4-platform").glob("ch*.md"))),
    ("Part V — 生產維運", sorted((BOOK / "part-5-operations").glob("ch*.md"))),
    ("Part VI — 前沿與職涯", sorted((BOOK / "part-6-frontier").glob("ch*.md"))),
    ("附錄", sorted((BOOK / "appendix").glob("*.md"))),
    ("內部文件（_meta）", [
        BOOK / "_meta" / "landscape-2026.md",
        BOOK / "_meta" / "maintenance.md",
        BOOK / "_meta" / "outline.md",
        BOOK / "_meta" / "style-guide.md",
    ]),
]


def title_of(path: Path, text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def build_manifest():
    chapters = []
    missing = []
    for group, files in GROUPS:
        for f in files:
            if not f.exists():
                missing.append(str(f))
                continue
            text = f.read_text(encoding="utf-8")
            chapters.append({
                "id": f.stem,
                "file": f.name,
                "group": group,
                "title": title_of(f, text),
                "md": text,
            })
    if missing:
        print("⚠️  缺少檔案（已略過）:\n  " + "\n  ".join(missing), file=sys.stderr)
    return chapters


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>從後端到 AI Infra — 閱讀器</title>
<style>
:root{ --fs:18px; --lh:1.95; --ls:0.02em; --ps:1.0; --pw:52; }
/* 等寬字型度量修正：把 CJK fallback 用 size-adjust 精確縮放成 Menlo 半形寬的 2 倍
   （Menlo advance = 0.60205em → 2× = 120.4%），讓 ASCII 圖裡的中文不再跑版 */
@font-face{font-family:"PreMono";src:local("Menlo")}
@font-face{font-family:"PreMonoCJK";src:local("PingFang TC"),local("PingFangTC-Regular"),local("PingFang SC"),local("PingFangSC-Regular");size-adjust:120.4%}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"PingFang TC","Noto Sans TC",sans-serif}
/* ---------- 主題 ---------- */
body[data-theme="paper"]{--bg:#f7f2e9;--fg:#2f2b24;--muted:#8d8474;--border:#e2d9c6;--codebg:#efe8d7;--link:#a05a17;--accent:#b06a1e;--side:#f0e9d8;--sideactive:#e4d9bf}
body[data-theme="light"]{--bg:#ffffff;--fg:#24292f;--muted:#6e7781;--border:#e8eaed;--codebg:#f5f7f9;--link:#0a69c2;--accent:#0a69c2;--side:#f7f8fa;--sideactive:#e9edf2}
body[data-theme="sepia"]{--bg:#f4ecd8;--fg:#52432e;--muted:#9b8a6d;--border:#dfd2b3;--codebg:#ebdfc3;--link:#985a1f;--accent:#985a1f;--side:#eee2c8;--sideactive:#e2d3ae}
body[data-theme="dark"]{--bg:#22262c;--fg:#c4ccd4;--muted:#828d99;--border:#3a424b;--codebg:#2b323a;--link:#7ab8f5;--accent:#7ab8f5;--side:#1d2126;--sideactive:#2e353d}
body{background:var(--bg);color:var(--fg)}
a{color:var(--link)}
/* ---------- 版面 ---------- */
#layout{display:flex;height:100%}
#sidebar{width:288px;min-width:288px;background:var(--side);border-right:1px solid var(--border);overflow-y:auto;padding:14px 0 40px;transition:transform .2s}
#main{flex:1;overflow-y:auto;position:relative;scroll-behavior:auto}
/* ---------- 側欄 ---------- */
#sidebar .brand{font-weight:700;font-size:15px;padding:6px 18px 12px;line-height:1.5}
#sidebar .grp{font-size:12px;color:var(--muted);font-weight:600;letter-spacing:.05em;padding:14px 18px 4px}
#sidebar a.ch{display:block;padding:6px 18px;font-size:13.5px;line-height:1.5;color:var(--fg);text-decoration:none;border-left:3px solid transparent}
#sidebar a.ch:hover{background:var(--sideactive)}
#sidebar a.ch.active{background:var(--sideactive);border-left-color:var(--accent);font-weight:600}
#sidebar .allbtn{margin:16px 18px 0;display:block;text-align:center;padding:8px;border:1px solid var(--border);border-radius:8px;font-size:13px;color:var(--fg);text-decoration:none;background:var(--bg)}
/* ---------- 頂欄 ---------- */
#topbar{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:8px;padding:10px 16px;background:var(--bg);border-bottom:1px solid var(--border)}
#topbar .ttl{flex:1;font-size:13.5px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.btn{cursor:pointer;border:1px solid var(--border);background:var(--bg);color:var(--fg);border-radius:8px;padding:6px 11px;font-size:14px;line-height:1}
.btn:hover{background:var(--codebg)}
#hamburger{display:none}
/* ---------- 內文 ---------- */
.prose{max-width:calc(var(--pw)*1rem);margin:0 auto;padding:2.4rem 1.7rem 3rem;font-size:var(--fs);line-height:var(--lh);letter-spacing:var(--ls)}
body[data-font="sans"] .prose{font-family:-apple-system,BlinkMacSystemFont,"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif}
body[data-font="serif"] .prose{font-family:"Songti TC","Noto Serif TC",Georgia,"PMingLiU",serif}
.prose p{margin:calc(var(--ps)*1em) 0}
.prose h1{font-size:1.5em;line-height:1.45;margin:.2em 0 .9em}
.prose h2{font-size:1.3em;line-height:1.45;margin:2em 0 .8em;padding-bottom:.35em;border-bottom:1px solid var(--border)}
.prose h3{font-size:1.13em;margin:1.7em 0 .6em}
.prose h4{font-size:1.02em;margin:1.4em 0 .5em}
.prose li{margin:.45em 0}
.prose ul,.prose ol{padding-left:1.6em}
.prose blockquote{margin:1.3em 0;padding:.7em 1.2em;border-left:4px solid var(--accent);background:var(--codebg);border-radius:0 8px 8px 0}
.prose blockquote p{margin:.5em 0}
.prose hr{border:none;border-top:1px solid var(--border);margin:2.4em 0}
.prose img{max-width:100%}
.prose pre{background:var(--codebg);border:1px solid var(--border);border-radius:8px;padding:.9em 1.1em;overflow-x:auto;font-size:.84em;line-height:1.6;letter-spacing:0;font-family:"PreMono","PreMonoCJK",Menlo,ui-monospace,monospace}
.prose pre code{background:none;padding:0;border:none;font-size:1em}
.prose code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"PingFang TC",monospace;background:var(--codebg);border:1px solid var(--border);border-radius:5px;padding:.08em .35em;font-size:.86em;letter-spacing:0}
.prose table{border-collapse:collapse;display:block;overflow-x:auto;margin:1.3em 0;font-size:.9em;line-height:1.65;letter-spacing:0}
.prose th,.prose td{border:1px solid var(--border);padding:.5em .75em;text-align:left;vertical-align:top}
.prose th{background:var(--codebg);white-space:nowrap}
/* ---------- 章尾導覽 ---------- */
#pager{max-width:calc(var(--pw)*1rem);margin:0 auto;padding:0 1.7rem 5rem;display:flex;gap:12px;justify-content:space-between}
#pager .btn{flex:1;text-align:center;padding:13px;font-size:14px;max-width:48%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
/* ---------- 設定面板 ---------- */
#panel{position:fixed;top:0;right:0;height:100%;width:300px;background:var(--side);border-left:1px solid var(--border);z-index:20;padding:18px 20px 40px;overflow-y:auto;transform:translateX(105%);transition:transform .2s;box-shadow:-6px 0 24px rgba(0,0,0,.08)}
#panel.open{transform:none}
#panel h3{margin:4px 0 14px;font-size:16px}
#panel .row{margin:0 0 16px}
#panel label{display:flex;justify-content:space-between;font-size:13px;color:var(--muted);margin-bottom:6px}
#panel input[type=range]{width:100%}
#panel .seg{display:flex;gap:6px;flex-wrap:wrap}
#panel .seg .btn{flex:1;min-width:56px;text-align:center;font-size:13px}
#panel .seg .btn.on{background:var(--accent);color:var(--bg);border-color:var(--accent)}
#backdrop{position:fixed;inset:0;background:rgba(0,0,0,.25);z-index:9;display:none}
#backdrop.show{display:block}
/* ---------- 手機 ---------- */
@media (max-width:880px){
  #sidebar{position:fixed;left:0;top:0;height:100%;z-index:15;transform:translateX(-102%)}
  #sidebar.open{transform:none;box-shadow:6px 0 24px rgba(0,0,0,.15)}
  #hamburger{display:inline-block}
  .prose{padding:1.6rem 1.1rem 2.5rem}
}
</style>
</head>
<body data-theme="paper" data-font="sans">
<div id="layout">
  <nav id="sidebar"></nav>
  <div id="main">
    <div id="topbar">
      <button class="btn" id="hamburger">☰</button>
      <span class="ttl" id="topttl"></span>
      <button class="btn" id="prevtop" title="上一章">←</button>
      <button class="btn" id="nexttop" title="下一章">→</button>
      <button class="btn" id="gear" title="閱讀設定">Aa</button>
    </div>
    <article class="prose" id="content"></article>
    <div id="pager">
      <button class="btn" id="prevbtn"></button>
      <button class="btn" id="nextbtn"></button>
    </div>
  </div>
</div>
<div id="backdrop"></div>
<aside id="panel">
  <h3>閱讀設定</h3>
  <div class="row"><label>主題</label>
    <div class="seg" id="themeseg">
      <button class="btn" data-v="paper">紙感</button>
      <button class="btn" data-v="light">純白</button>
      <button class="btn" data-v="sepia">米褐</button>
      <button class="btn" data-v="dark">深色</button>
    </div></div>
  <div class="row"><label>字體</label>
    <div class="seg" id="fontseg">
      <button class="btn" data-v="sans">黑體</button>
      <button class="btn" data-v="serif">明體</button>
    </div></div>
  <div class="row"><label>字級 <output id="o_fs"></output></label>
    <input type="range" id="r_fs" min="15" max="24" step="0.5"></div>
  <div class="row"><label>行距 <output id="o_lh"></output></label>
    <input type="range" id="r_lh" min="1.5" max="2.4" step="0.05"></div>
  <div class="row"><label>字距 <output id="o_ls"></output></label>
    <input type="range" id="r_ls" min="0" max="0.12" step="0.01"></div>
  <div class="row"><label>段距 <output id="o_ps"></output></label>
    <input type="range" id="r_ps" min="0.5" max="2" step="0.1"></div>
  <div class="row"><label>欄寬 <output id="o_pw"></output></label>
    <input type="range" id="r_pw" min="32" max="76" step="1"></div>
  <div class="row"><button class="btn" id="resetbtn" style="width:100%">恢復預設</button></div>
  <div class="row" style="font-size:12px;color:var(--muted)">建置於 __BUILDDATE__ ・內容基準 2026-06<br>更新書後重跑 <code>python3 web/build_reader.py</code></div>
</aside>

<script id="bookdata" type="application/json">__BOOKDATA__</script>
<script>__MARKED__</script>
<script>
(function(){
"use strict";
var DATA=JSON.parse(document.getElementById('bookdata').textContent);
var CHS=DATA.chapters, byId={}, byFile={};
CHS.forEach(function(c){byId[c.id]=c;byFile[c.file]=c;});

function lsGet(k,d){try{var v=localStorage.getItem(k);return v===null?d:JSON.parse(v);}catch(e){return d;}}
function lsSet(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch(e){}}

var DEF={theme:'paper',font:'sans',fs:18,lh:1.95,ls:0.02,ps:1.0,pw:52};
var prefs=Object.assign({},DEF,lsGet('aiib.prefs2',{}));

var main=document.getElementById('main'),content=document.getElementById('content');
var cur=null;

function applyPrefs(){
  document.body.dataset.theme=prefs.theme;
  document.body.dataset.font=prefs.font;
  var r=document.documentElement.style;
  r.setProperty('--fs',prefs.fs+'px');
  r.setProperty('--lh',prefs.lh);
  r.setProperty('--ls',prefs.ls+'em');
  r.setProperty('--ps',prefs.ps);
  r.setProperty('--pw',prefs.pw);
  ['fs','lh','ls','ps','pw'].forEach(function(k){
    var ri=document.getElementById('r_'+k),oi=document.getElementById('o_'+k);
    if(ri){ri.value=prefs[k];} if(oi){oi.textContent=prefs[k];}
  });
  document.querySelectorAll('#themeseg .btn').forEach(function(b){b.classList.toggle('on',b.dataset.v===prefs.theme);});
  document.querySelectorAll('#fontseg .btn').forEach(function(b){b.classList.toggle('on',b.dataset.v===prefs.font);});
  lsSet('aiib.prefs2',prefs);
}

function buildSidebar(){
  var sb=document.getElementById('sidebar');
  var html='<div class="brand">從後端到 AI Infra<br><span style="font-weight:400;font-size:12px;color:var(--muted)">LLM 推論基礎設施工程</span></div>';
  var g='';
  CHS.forEach(function(c){
    if(c.group!==g){g=c.group;html+='<div class="grp">'+g+'</div>';}
    html+='<a class="ch" data-id="'+c.id+'" href="#'+c.id+'">'+c.title.replace(/：.*$/,'')+'</a>';
  });
  html+='<a class="allbtn" href="#_all">整本單頁（供全文 ⌘F 搜尋）</a>';
  sb.innerHTML=html;
  sb.addEventListener('click',function(e){
    var a=e.target.closest('a');if(!a)return;
    e.preventDefault();
    show(a.dataset.id||a.getAttribute('href').slice(1));
    if(window.innerWidth<=880){sb.classList.remove('open');backdrop.classList.remove('show');}
  });
}

function flatIndex(id){for(var i=0;i<CHS.length;i++){if(CHS[i].id===id)return i;}return -1;}

function postprocess(){
  content.querySelectorAll('a[href]').forEach(function(a){
    var h=a.getAttribute('href');
    if(/^https?:/i.test(h)){a.target='_blank';a.rel='noopener';return;}
    var m=h.match(/([^\/#]+\.md)/);
    if(m&&byFile[m[1]]){
      var id=byFile[m[1]].id;
      a.setAttribute('href','#'+id);
      a.addEventListener('click',function(e){e.preventDefault();show(id);});
    }
  });
}

var suppressHash=false;
function show(id){
  var ch;
  if(id==='_all'){
    ch={id:'_all',title:'整本（單頁）',md:CHS.map(function(c){return c.md;}).join('\n\n---\n\n')};
  }else{
    ch=byId[id]||CHS[0];
  }
  cur=ch.id;
  content.innerHTML=marked.parse(ch.md);
  postprocess();
  document.getElementById('topttl').textContent=ch.title;
  document.title=ch.title+' — AI Infra 書';
  var i=flatIndex(ch.id);
  var prev=i>0?CHS[i-1]:null, next=(i>=0&&i<CHS.length-1)?CHS[i+1]:null;
  var pb=document.getElementById('prevbtn'),nb=document.getElementById('nextbtn');
  pb.style.visibility=prev?'visible':'hidden';
  nb.style.visibility=next?'visible':'hidden';
  if(prev)pb.textContent='← '+prev.title;
  if(next)nb.textContent=next.title+' →';
  pb.onclick=prev?function(){show(prev.id);}:null;
  nb.onclick=next?function(){show(next.id);}:null;
  document.getElementById('prevtop').onclick=prev?function(){show(prev.id);}:null;
  document.getElementById('nexttop').onclick=next?function(){show(next.id);}:null;
  document.querySelectorAll('#sidebar a.ch').forEach(function(a){a.classList.toggle('active',a.dataset.id===cur);});
  if(location.hash.slice(1)!==cur){suppressHash=true;location.hash=cur;}
  lsSet('aiib.last',cur);
  main.scrollTop=lsGet('aiib.scroll.'+cur,0);
}

var scrollTimer=null;
main.addEventListener('scroll',function(){
  if(scrollTimer)clearTimeout(scrollTimer);
  scrollTimer=setTimeout(function(){if(cur)lsSet('aiib.scroll.'+cur,main.scrollTop);},250);
});

window.addEventListener('hashchange',function(){
  if(suppressHash){suppressHash=false;return;}
  var h=location.hash.slice(1);
  if(h&&h!==cur)show(h);
});

document.addEventListener('keydown',function(e){
  var t=e.target.tagName;
  if(t==='INPUT'||t==='TEXTAREA')return;
  if(e.key==='ArrowLeft'){var b=document.getElementById('prevbtn');if(b.onclick)b.onclick();}
  if(e.key==='ArrowRight'){var b2=document.getElementById('nextbtn');if(b2.onclick)b2.onclick();}
});

/* 設定面板 */
var panel=document.getElementById('panel'),backdrop=document.getElementById('backdrop');
document.getElementById('gear').onclick=function(){panel.classList.toggle('open');backdrop.classList.toggle('show',panel.classList.contains('open'));};
backdrop.onclick=function(){panel.classList.remove('open');document.getElementById('sidebar').classList.remove('open');backdrop.classList.remove('show');};
document.getElementById('hamburger').onclick=function(){document.getElementById('sidebar').classList.add('open');backdrop.classList.add('show');};
document.getElementById('themeseg').addEventListener('click',function(e){var b=e.target.closest('.btn');if(b){prefs.theme=b.dataset.v;applyPrefs();}});
document.getElementById('fontseg').addEventListener('click',function(e){var b=e.target.closest('.btn');if(b){prefs.font=b.dataset.v;applyPrefs();}});
[['fs',parseFloat],['lh',parseFloat],['ls',parseFloat],['ps',parseFloat],['pw',parseFloat]].forEach(function(p){
  document.getElementById('r_'+p[0]).addEventListener('input',function(e){prefs[p[0]]=p[1](e.target.value);applyPrefs();});
});
document.getElementById('resetbtn').onclick=function(){prefs=Object.assign({},DEF);applyPrefs();};

/* 啟動 */
applyPrefs();
buildSidebar();
var start=location.hash.slice(1)||lsGet('aiib.last',CHS[0].id);
show(byId[start]||start==='_all'?start:CHS[0].id);
})();
</script>
</body>
</html>
"""


def main():
    if not VENDOR.exists():
        sys.exit("找不到 web/vendor/marked.min.js — 請先下載（見 README 或重新 curl jsdelivr marked@12.0.2）")
    chapters = build_manifest()
    if not chapters:
        sys.exit("book/ 下沒有任何章節檔案")
    data = json.dumps({"chapters": chapters}, ensure_ascii=False).replace("</", "<\\/")
    marked_src = VENDOR.read_text(encoding="utf-8").replace("</script", "<\\/script")
    html = (TEMPLATE
            .replace("__BOOKDATA__", data)
            .replace("__MARKED__", marked_src)
            .replace("__BUILDDATE__", date.today().isoformat()))
    OUT.write_text(html, encoding="utf-8")
    size_mb = OUT.stat().st_size / 1024 / 1024
    print(f"✅ 已輸出 {OUT}（{size_mb:.2f} MB，{len(chapters)} 個章節/文件）")


if __name__ == "__main__":
    main()
