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
rep("function render(){", 'function render(){\n  if(tab!=="apps" && tab!=="backup") tab="apps";   // forms app: only applications and settings')

s = s.replace('"No roll loaded yet"', '"Set your part in Account settings"')
# ---- sign-in screen wording ----
rep("<div><h2>Keep your part's roll safe</h2><p class=\"muted small\" style=\"margin:6px 0 0\">Free for every BLO. Sign in with your email so your voter list is saved to your own private account and comes back on any phone.</p></div>",
    "<div><h2>BLO Forms</h2><p class=\"muted small\" style=\"margin:6px 0 0\">Fill Form 6, 7 and 8 office papers and download them as one PDF. Free for every BLO. Sign in so your applications are saved to your own account and come back on any phone.</p></div>")
s = s.replace("Your data stays on this phone; download Excel backups often.", "Your applications stay on this phone only.")
s = s.replace('$("#partLine").textContent="Your part\'s voter register";', '$("#partLine").textContent="Forms for BLOs";')

# ---- Account settings: account, part details, signature only ----
for item in ['{ id:"backup",', '{ id:"restore",', '{ id:"recent",', '{ id:"fresh",']:
    i = s.index(item, s.index("function renderBackup")); j = s.index("\n", i); s = s[:i] + s[j+1:]
i = s.index('if(t==="backup") return [['); j = s.index("\n", i)
s = s[:i] + '''if(t==="backup") return [["👤",session&&session.token?"Your account":"Create a free account",()=>{ window._accSec="account"; }],["🗳","My part details",()=>{ window._accSec="part"; }],["✍","My signature",()=>{ window._accSec="sign"; }]];''' + s[j:]

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
async function uploadList(){}
function askAddToRoll(){}
function rollAction(){ return null; }
'''
anchor = "/* ================= start ================= */"
rep(anchor, over + anchor)
# no "add to voter list" / roll lookups in the sent bar
s = s.replace('${a.addedVoterId&&vIndex(a.addedVoterId)>=0?`<button class="btn primary" id="apOpenV">Open in voter list</button>`:rollAction(a)?', '${false?"":rollAction(a)?')

open("/home/claude/blo-register/blo-forms/index.html", "w").write(s)
print("ok", len(s))
