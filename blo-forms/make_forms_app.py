"""Builds the BLO Forms app (applications only) from the main BLO Roll Register app.
Run after changing index.html:  python3 make_forms_app.py  -> blo-forms/index.html"""
import re, sys
src = open("/home/claude/blo-register/index.html").read()
s = src
def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    if n != cnt: sys.exit(f"pattern found {n}x (want {cnt}): {old[:80]}")
    s = s.replace(old, new)

# ---- name, storage keys (separate from the roll app), files ----
rep("<title>BLO Roll Register</title>", "<title>BLO Forms</title>")
rep("<h1>BLO Roll Register</h1>", "<h1>BLO Forms</h1>")
rep('<b>BLO Register</b></div>', '<b>BLO Forms</b></div>')
s = s.replace('"bloreg:session"', '"blofm:session"').replace('"bloreg:data:', '"blofm:data:').replace('"bloreg:pending-upload"', '"blofm:pending-upload"')
s = s.replace('"bloreg:older-phone-copy:', '"blofm:older-phone-copy:')
s = s.replace('"file": "forms/', '"file": "../forms/').replace('"file":"forms/', '"file":"../forms/')
s = re.sub(r'"forms/(f6-approve|f6-reject|f7-death|f7-double|f7-migration|f7-panchanama|f8-correction|f8-shifting|f12-shifting|declaration-annex4)\.pdf"', r'"../forms/\1.pdf"', s)
rep('<meta name="theme-color" content="#5A2DA3">', '<meta name="theme-color" content="#1D5C8F">')
rep('<link rel="icon" href="icon-192.png">', '<link rel="icon" href="../icon-192.png">')
rep('<link rel="apple-touch-icon" href="icon-192.png">', '<link rel="apple-touch-icon" href="../icon-192.png">')

# ---- left rail: Applications and Account settings only ----
rail = s[s.index('<nav class="tabs" id="tabs"'):s.index('</nav>', s.index('<nav class="tabs" id="tabs"'))]
keep = []
for line in rail.split("\n"):
    if "<button data-tab=" in line and not ('data-tab="apps"' in line or 'data-tab="backup"' in line): continue
    keep.append(line)
s = s.replace(rail, "\n".join(keep))
rep('let tab = "home";', 'let tab = "apps";')
rep("const FORMS_ONLY=false;", "const FORMS_ONLY=true;")
rep("function render(){", 'function render(){\n  if(tab!=="apps" && tab!=="backup") tab="apps";   // forms app: only applications and settings')

s = s.replace('"No roll loaded yet"', '"Set your part in Account settings"')
# ---- sign-in screen wording ----
rep("<div><h2>Keep your part's roll safe</h2><p class=\"muted small\" style=\"margin:6px 0 0\">Free for every BLO. Sign in with your email so your voter list is saved to your own private account and comes back on any phone.</p></div>",
    """<div class="hero">
      <span class="hero-o o1"></span><span class="hero-o o2"></span>
      <div class="hero-row">
        <div class="hero-l"><span class="hero-pill">✦ FREE FOR EVERY BLO</span><h1 class="hero-t">BLO <span>Forms</span></h1></div>
        <p class="hero-big">No writing.<br><em>Only online.</em></p>
      </div>
      <div class="hero-f"><span>⚡ Fill in minutes</span><span>📄 Ready PDF</span><span>📱 Any phone</span></div>
    </div>
    <p class="hero-in">Sign in to keep your applications safe in your own account — they come back on any phone.</p>""")
s = s.replace('<div class="auth-tabs"><button data-m="login"', '''<div class="card sample-card"><div><b>👁 See a sample filled PDF</b> <span class="tap-here">👇 Click here</span><div class="muted small">Example papers the app makes — no sign-in needed.</div></div>
      <div class="row" style="gap:6px;flex-wrap:wrap"><button class="btn" data-sample="f6">Form 6 + check slip</button><button class="btn" data-sample="f7">Form 7 (death)</button><button class="btn" data-sample="f8">Form 8 (shifting)</button></div></div>
    <div class="auth-tabs"><button data-m="login"''', 1)
s = s.replace("  bindInstall();\n  $(\"#deviceMode\").onclick", "  bindInstall();\n  v.querySelectorAll(\"[data-sample]\").forEach(b=>b.onclick=()=>showSample(b.dataset.sample));\n  $(\"#deviceMode\").onclick", 1)
s = s.replace("Your data stays on this phone; download Excel backups often.", "Your applications stay on this phone only.")
s = s.replace('$("#partLine").textContent="Your part\'s voter register";', '$("#partLine").textContent="Forms for BLOs";')

# ---- Account settings: account, part details, signature only ----
for item in ['{ id:"backup",', '{ id:"restore",', '{ id:"recent",', '{ id:"fresh",']:
    i = s.index(item, s.index("function renderBackup")); j = s.index("\n", i); s = s[:i] + s[j+1:]
i = s.index('if(t==="backup") return [['); j = s.index("\n", i)
s = s[:i] + '''if(t==="backup") return [["👤",session&&session.token?"Your account":"Create a free account",()=>{ window._accSec="account"; }],["🗳","My part details",()=>{ window._accSec="part"; }],["✍","My signature",()=>{ window._accSec="sign"; }],["🏛","Officer (ERO) name",()=>{ window._accSec="ero"; }]];''' + s[j:]

# ---- overrides: own cloud store, no voter list ----
over = r'''
/* ================= BLO Forms: own store (blo_forms_*), never touches the voter roll ================= */
async function flushCloud(){
  if(!cloud.ready) return;
  if(cloud.busy){ cloud.again=true; return; }
  cloud.busy=true; cloud.dirty.clear(); const stamp=state.savedAt;
  try{ await rpc("blo_forms_save",{ p_token:session.token, p_data:state.meta, p_saved_at:stamp }); state.cloudSavedAt=stamp; saveLocal(); setSync("saved","Saved to account"); }
  catch(e){ if(e.code==="not_signed_in"){ setSync("error","Signed out · saved on phone"); cloud.ready=false; toast(e.message); }
    else { setSync("error", navigator.onLine===false ? "Offline · saved on phone" : "Saved on phone · retrying"); setTimeout(scheduleCloud, 15000); } }
  finally{ cloud.busy=false; if(cloud.again){ cloud.again=false; scheduleCloud(); } }
}
async function connectAccount(){
  const local = lsGet(dataKey());
  if(local && local.meta){ state=Object.assign(blank(),local); state.meta=Object.assign(blank().meta,local.meta); state.voters=[]; }
  showApp(); setSync("saving","Loading account…");
  try{
    const r = await rpc("blo_forms_load",{ p_token:session.token });
    if(r.exists && (r.saved_at||0) >= (state.savedAt||0)){
      state = { meta:Object.assign(blank().meta, r.data||{}), voters:[], savedAt:r.saved_at||0, cloudSavedAt:r.saved_at||0 };
      saveLocal(); cloud.ready=true; setSync("saved","Saved to account"); render();
    } else {
      if(!r.exists && r.roll_meta){ for(const [k,v] of Object.entries(r.roll_meta)) if(v!=null && !state.meta[k]) state.meta[k]=v; state.savedAt=Date.now(); }
      cloud.ready=true; render();
      if(state.savedAt){ scheduleCloud(); } else setSync("saved","Account ready");
    }
  }catch(e){
    if(e.code==="not_signed_in"){ lsSet("blofm:session", null); session=null; toast(e.message); showAuth(); return; }
    setSync("error","Offline · saved on phone"); setTimeout(()=>{ if(!cloud.ready && session && session.token) connectAccount(); }, 20000);
  }
}
function syncLists(){}
/* sample papers on the sign-in screen (marked SAMPLE) */
function sampleApp(k){
  const d=n=>{ const t=new Date(Date.now()+n*864e5); return t.toISOString().slice(0,10); };
  const base={ sample:true, id:"sample", refNo:"S01150O6N0000000000001", appDate:d(-6), noticeDate:d(-4), hearDate:d(4), hearTime:"11:00 AM", hearPlace:"GUNTAKAL MUNICIPALITY", orderDate:d(10), town:"GUNTAKAL", area:"SAMPLE COLONY", partNo:"159", mandal:"GUNTAKAL", history:[], docs:{} };
  const A={
    f6:Object.assign({},base,{ type:"f6", f6out:"approve", name:"RAVI KUMAR", relType:"Father", relName:"SURESH KUMAR", gender:"M", dob:"2007-06-15", house:"1-2-3", area:"SAMPLE STREET", phone:"9000000001", decl:true,
      ecPdf:{ url:"../forms/sample-check-slip.pdf", name:"sample-check-slip.pdf" }, eciChk:Object.assign(eciDefaults("yes"),{ place:"GUNTAKAL" }),
      d4:{ use:true, sir:"rel", e:{}, r:{Name:"SURESH KUMAR", Rel:"NARAYANA", RelType:"Father", State:"Andhra Pradesh", Dist:"Anantapur", AcNo:"170", AcName:"Gooty", Part:"112", Sr:"487"}, f:{fName:"SURESH KUMAR", mName:"LAKSHMI DEVI"} } }),
    f7:Object.assign({},base,{ type:"f7", f7why:"death", deathProof:"panch", refNo:"F7-SAMPLE-0001", name:"RAMESH KUMAR", relType:"Father", relName:"NARAYANA", house:"1-245",
      del:{ name:"NARAYANA REDDY", relName:"VENKATA REDDY", relation:"FATHER", house:"2-118", village:"GUNTAKAL", mandal:"GUNTAKAL", part:"159", serial:"487", age:"78", deathDate:d(-90) },
      panchDate:d(-3), panch:["K. RAMANA","S. LAKSHMI","P. SURESH","M. ANJI"] }),
    f8:Object.assign({},base,{ type:"f8", req:"Shifting of residence", refNo:"S01150O8N0000000000002", name:"LAKSHMI DEVI", relType:"Husband", relName:"SURESH", house:"3-77", area:"NEW COLONY" })
  };
  return A[k];
}
/* samples are ready-made pictures + PDF files, so they open on every phone (no PDF maker needed) */
const SAMPLE_PAGES=__SAMPLE_PAGES__;
function showSample(k){
  const n=SAMPLE_PAGES[k]||0; if(!n){ previewFormPdf(sampleApp(k)); return; }
  const nm={f6:"Form 6 + check slip",f7:"Form 7 (death)",f8:"Form 8 (shifting)"}[k]||"Sample";
  const ov=document.createElement("div"); ov.className="pv-bg"; ov.setAttribute("role","dialog"); ov.setAttribute("aria-label","Sample PDF");
  let pages=""; for(let i=1;i<=n;i++) pages+=`<div class="pv-page"><div class="pv-pn">Page ${i} of ${n}</div><img src="../forms/samples/${k}-${i}.jpg" alt="Sample page ${i}" loading="${i<3?"eager":"lazy"}" style="width:100%;display:block;background:#fff"></div>`;
  ov.innerHTML=`<div class="pv-band"><div style="min-width:0"><div class="pv-k">Sample</div><div class="pv-n">${esc(nm)}</div></div>
    <div class="row pv-act"><button class="btn" id="pvEd">✕ Close</button><a class="btn primary" id="pvDl" style="text-decoration:none" href="../forms/samples/sample-${k}.pdf" download="BLO-Forms-sample-${k}.pdf">⬇ Download PDF</a></div></div>
    <div class="pv-pages">${pages}</div>`;
  document.body.appendChild(ov); ov.querySelector("#pvEd").onclick=()=>ov.remove();
}
async function uploadList(){}
function askAddToRoll(){}
function rollAction(){ return null; }
'''
anchor = "/* ================= start ================= */"
s = s.replace("/* compact home */", ".sample-card{display:flex;flex-direction:column;gap:10px;border:2px solid var(--accent)}\n/* compact home */", 1)
HERO_CSS = r'''.hero{position:relative;overflow:hidden;border-radius:22px;padding:22px 18px 16px;text-align:center;color:#fff;background:linear-gradient(140deg,#24104F 0%,#4B1FA0 45%,#8A2D6B 100%);box-shadow:0 14px 34px rgba(59,29,122,.35);isolation:isolate}
.hero-o{position:absolute;border-radius:50%;z-index:-1;filter:blur(2px)}
.hero-o.o1{width:190px;height:190px;right:-60px;top:-70px;background:radial-gradient(circle,#FFB84D88,transparent 70%)}
.hero-o.o2{width:220px;height:220px;left:-90px;bottom:-110px;background:radial-gradient(circle,#4DD0FF66,transparent 70%)}
.hero-pill{display:inline-block;font-size:.62rem;font-weight:900;letter-spacing:.14em;padding:4px 12px;border-radius:999px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.3)}
.hero-t{margin:12px 0 2px;font-family:var(--f-display);font-weight:900;font-size:clamp(2.1rem,11vw,2.9rem);line-height:1;letter-spacing:-.01em;text-shadow:0 3px 14px rgba(0,0,0,.3)}
.hero-t span{background:linear-gradient(90deg,#FFD24D,#FF9F43);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero-big{margin:12px 0 6px;font-family:var(--f-display);font-weight:850;font-size:clamp(1.35rem,7vw,1.75rem);line-height:1.15}
.hero-big em{font-style:normal;color:#FFD24D;position:relative;white-space:nowrap}
.hero-big em::after{content:"";position:absolute;left:0;right:0;bottom:-3px;height:3px;border-radius:3px;background:linear-gradient(90deg,#FFD24D,#FF9F43);animation:heroLine 2.4s ease-in-out infinite;transform-origin:left}
@keyframes heroLine{0%{transform:scaleX(0)}45%,100%{transform:scaleX(1)}}
.hero-sub{margin:8px auto 14px;max-width:30ch;font-size:.9rem;line-height:1.4;color:rgba(255,255,255,.88)}
.hero-f{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.hero-f span{display:flex;flex-direction:column;align-items:center;gap:3px;font-size:.7rem;font-weight:750;line-height:1.2;padding:9px 4px;border-radius:12px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2)}
.hero-f b{font-size:1.25rem}
.hero-by{margin-top:14px;font-size:.6rem;font-weight:800;letter-spacing:.12em;opacity:.9}
.hero-by b{color:#FFD24D;font-weight:900}
.hero-in{margin:0;text-align:center;font-size:.86rem;color:var(--muted)}
@media (prefers-reduced-motion:reduce){.hero-big em::after{animation:none}}
.hero{padding:12px 14px 10px;border-radius:18px;text-align:left}
.hero-row{display:flex;align-items:center;justify-content:space-between;gap:10px}
.hero-l{min-width:0}
.hero-pill{font-size:.52rem;padding:2px 8px;letter-spacing:.1em}
.hero-t{margin:5px 0 0;font-size:clamp(1.55rem,8vw,2rem)}
.hero-big{margin:0;text-align:right;font-size:clamp(.98rem,4.6vw,1.2rem);line-height:1.2;flex:none}
.hero-big em::after{bottom:-2px;height:2px}
.hero-f{display:flex;gap:6px;margin-top:9px;grid-template-columns:none}
.hero-f span{flex:1;flex-direction:row;justify-content:center;gap:4px;font-size:.66rem;padding:5px 4px;border-radius:999px;white-space:nowrap}
'''
s = s.replace("/* compact home */", HERO_CSS + "/* compact home */", 1)
rep(anchor, over + anchor)
# no "add to voter list" / roll lookups in the sent bar
s = s.replace('${a.addedVoterId&&vIndex(a.addedVoterId)>=0?`<button class="btn primary" id="apOpenV">Open in voter list</button>`:rollAction(a)?', '${false?"":rollAction(a)?')

exec(open("/home/claude/blo-register/forms_signin.py").read())
import os, json as _json
_sd = "/home/claude/blo-roll-register/forms/samples"
_cnt = {k: len([f for f in os.listdir(_sd) if f.startswith(k+"-") and f.endswith(".jpg")]) if os.path.isdir(_sd) else 0 for k in ("f6","f7","f8")}
s = s.replace("__SAMPLE_PAGES__", _json.dumps(_cnt))
open("/home/claude/blo-register/blo-forms/index.html", "w").write(s)
print("ok", len(s))
