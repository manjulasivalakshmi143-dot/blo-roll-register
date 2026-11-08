# ---- sign-in page: two choices first; the sign-in form opens only after "With sign in" ----
# (run from make_forms_app.py on the string s)
i = s.index('<p class="hero-in">'); j = s.index('</p>', i) + 4
s = s[:i] + """<div class="mode-pick">
      <button type="button" class="mode-btn on" id="mWith"><span class="mode-ic">🔐</span><span><b>With sign in</b><small>Your data is saved for next time — on any phone</small></span><span class="mode-go">›</span></button>
      <button type="button" class="mode-btn" id="mWithout"><span class="mode-ic">📱</span><span><b>Without sign in</b><small>Saved on this phone only — previous data may not be available</small></span><span class="mode-go">›</span></button>
    </div>
    <div id="signBox" class="sign-box" ${(window._signOpen||mode!=="login")?"":"hidden"}>""" + s[j:]
a = s.index('<div class="card sample-card">'); b = s.index('<div class="auth-tabs">', a)
sample = s[a:b]; s = s[:a] + s[b:]
k = s.index('</form>', a) + len('</form>')
s = s[:k] + '\n    </div>\n    ' + sample.strip() + s[k:]
s = s.replace('<div class="card small"><strong>No internet or no account?</strong>', '<div class="card small" hidden><strong>No internet or no account?</strong>', 1)
s = s.replace('  v.querySelectorAll("[data-m]").forEach(b=>b.onclick=()=>showAuth(b.dataset.m));',
 """  v.querySelectorAll("[data-m]").forEach(b=>b.onclick=()=>showAuth(b.dataset.m));
  $("#mWith").onclick=()=>{ window._signOpen=true; const sb=$("#signBox"); sb.hidden=false; sb.scrollIntoView({behavior:"smooth",block:"start"}); setTimeout(()=>{ const e=$("#aEmail"), pw=$("#aPass"); const t=(e&&e.value)?pw:e; if(t) t.focus(); },350); };
  $("#mWithout").onclick=()=>confirmBox("Use without sign in? Applications are saved on this phone only. If the phone is changed or the app data is cleared, previous data may not be available.","Continue",()=>$("#deviceMode").click());""", 1)
s = s.replace("/* compact home */", """.mode-pick{display:grid;gap:10px}
.mode-btn{display:grid;grid-template-columns:44px 1fr 18px;align-items:center;gap:10px;text-align:left;font:inherit;padding:14px;border-radius:16px;border:2px solid var(--line);background:var(--surface);color:var(--ink);cursor:pointer;box-shadow:0 4px 14px rgba(40,20,90,.08);transition:transform .1s}
.mode-btn:active{transform:scale(.98)}
.mode-btn b{display:block;font-family:var(--f-display);font-size:1.08rem;font-weight:800}
.mode-btn small{display:block;font-size:.8rem;color:var(--muted);line-height:1.3;margin-top:2px}
.mode-ic{width:44px;height:44px;border-radius:12px;display:grid;place-items:center;font-size:1.4rem;background:var(--accent-soft)}
.mode-go{font-size:1.5rem;color:var(--accent);font-weight:700}
.mode-btn.on{border-color:var(--accent);background:linear-gradient(135deg,#F3EDFF,#FFFFFF)}
.mode-btn.on .mode-ic{background:linear-gradient(140deg,#4B1FA0,#8A2D6B);color:#fff}
.sign-box{display:flex;flex-direction:column;gap:12px}
.sign-box[hidden]{display:none}
/* compact home */""", 1)
