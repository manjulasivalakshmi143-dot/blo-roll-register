"""Makes the published copies work on older Android phones too.
- CSS: every color-mix() gets a plain-colour line before it (older Chrome skips color-mix and uses that)
- inset:0 gets top/right/bottom/left; dvh heights get a % fallback
- JavaScript: newer syntax is converted for older Chrome (esbuild)
Usage: python3 build.py <in.html> <out.html>"""
import re, sys, subprocess, json

src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()

def split_args(t):
    out, depth, cur = [], 0, ""
    for ch in t:
        if ch == "(": depth += 1
        if ch == ")": depth -= 1
        if ch == "," and depth == 0: out.append(cur.strip()); cur = ""
        else: cur += ch
    out.append(cur.strip()); return out

def mix_fallback(m):
    # color-mix(in srgb, A p%, B)  -> A when p >= 50, otherwise B
    inner = m.group(1)
    a = split_args(inner)
    if len(a) < 3: return a[-1]
    A, B = a[1], a[2]
    pm = re.search(r"\s(\d+)%\s*$", A)
    pct = int(pm.group(1)) if pm else 50
    A = re.sub(r"\s\d+%\s*$", "", A)
    return A if pct >= 50 else B

def find_mix(t):
    """replace each color-mix(...) (balanced) using mix_fallback"""
    out, i = "", 0
    while True:
        j = t.find("color-mix(", i)
        if j < 0: return out + t[i:]
        k, depth = j + len("color-mix("), 1
        while depth:
            if t[k] == "(": depth += 1
            elif t[k] == ")": depth -= 1
            k += 1
        inner = t[j + len("color-mix("):k - 1]
        out += t[i:j] + mix_fallback(re.match(r"(.*)", inner, re.S)); i = k

def css_fix(css):
    # 1) declarations with color-mix: add a fallback declaration before
    def decl(m):
        d = m.group(0)
        if "color-mix(" not in d: return d
        return find_mix(d) + ";" + d
    css = re.sub(r"(?<=[{;])[^{};]*color-mix\([^{};]*", decl, css)
    # 2) inset:0
    css = re.sub(r"(?<=[{;])inset:0(?=[;}])", "top:0;right:0;bottom:0;left:0;inset:0", css)
    # 3) heights using dvh through var(--vhpx, 100dvh): give a plain fallback first
    css = css.replace("height:var(--vhpx,100dvh)", "height:100%;height:var(--vhpx,100dvh)")
    return css

def fix_styles(html):
    return re.sub(r"(<style>)(.*?)(</style>)", lambda m: m.group(1) + css_fix(m.group(2)) + m.group(3), html, flags=re.S)

s = fix_styles(s)
# older Chrome (before ~98): use pdf.js "legacy" build, which supports older browsers
tag = '<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>'
if tag in s:
    s = s.replace(tag, tag + """<script>(function(){ if('structuredClone' in window) return;
  var base='https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/legacy/build/';
  var x=document.createElement('script'); x.src=base+'pdf.min.js';
  x.onload=function(){ try{ var o=pdfjsLib.GlobalWorkerOptions; Object.defineProperty(o,'workerSrc',{get:function(){return base+'pdf.worker.min.js'},set:function(){}}); }catch(e){} };
  document.head.appendChild(x); })();</script>""", 1)

# JavaScript: convert the app's own (last, inline) script for older Chrome
a = s.rindex("<script>") + len("<script>"); b = s.rindex("</script>")
js = s[a:b]
r = subprocess.run(["node", "-e", """
const esb=require('/opt/npm-tools/node_modules/esbuild'); let src='';
process.stdin.on('data',d=>src+=d).on('end',()=>{ try{
  const out=esb.transformSync(src,{loader:'js',target:'chrome64',charset:'utf8',legalComments:'none'});
  process.stdout.write(out.code); }catch(e){ console.error(e.message); process.exit(1); } });
"""], input=js, capture_output=True, text=True)
if r.returncode != 0: sys.exit("esbuild failed: " + r.stderr[:2000])
s = s[:a] + "\n" + r.stdout + s[b:]
open(dst, "w").write(s)
print("built", dst, len(s))
