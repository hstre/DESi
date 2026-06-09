"""Reviewer Port — a local, graphical window into the router's decisions.

A dependency-free local web app (stdlib ``http.server``). For each query it
shows: the classified task, the routing decision (tool / local model / API model)
with its rationale, the answer (the tool answers live and offline; a model is
called only if configured and reachable), and the deterministic audit hash.

Run:
    python -m desi.reviewer_port                 # uses desi/config.json or the example
    python -m desi.reviewer_port --port 8765 --config /path/to/config.json

Then open http://localhost:8765 . Nothing leaves your machine unless you route
to an API provider.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from desi.engine import run
from desi.ledger import Ledger
from desi.policy import Constraints
from desi.providers import Registry, load_config
from desi.tool_registry import default_registry

_HERE = Path(__file__).resolve().parent


def _json_safe(obj):
    """Recursively replace non-finite floats (inf/nan) with None so the payload
    is valid JSON for the browser (json.dumps emits bare ``Infinity`` otherwise)."""
    import math

    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj

PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>DESi · Reviewer Port</title><style>
:root{--bg:#070a10;--panel:#0f1622;--line:#1c2737;--ink:#e8eef7;--muted:#8a99af;
--accent:#2ce6c4;--blue:#5aa8ff;--warn:#ff6b6b;--mono:ui-monospace,Menlo,Consolas,monospace}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.5}
.wrap{max-width:880px;margin:0 auto;padding:28px 20px}
h1{font-size:22px;margin:0 0 2px}h1 .d{color:var(--accent)}
.sub{color:var(--muted);font-size:13px;margin:0 0 22px}
textarea,select,input{background:var(--panel);color:var(--ink);border:1px solid var(--line);
border-radius:9px;padding:10px;font-size:14px;width:100%}
textarea{min-height:64px;resize:vertical}
.row{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0}
.row>div{flex:1;min-width:150px}label{font-size:12px;color:var(--muted);display:block;margin:0 0 4px}
button{background:var(--accent);color:#04110d;border:0;border-radius:9px;padding:11px 20px;
font-weight:700;font-size:14px;cursor:pointer;margin-top:6px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin:16px 0}
.k{font-family:var(--mono);font-size:11px;letter-spacing:1px;color:var(--muted);text-transform:uppercase}
.big{font-size:20px;font-weight:700;margin:2px 0 6px}
.tool{color:var(--accent)}.local{color:var(--blue)}.api{color:var(--warn)}
.rationale{color:var(--muted);font-size:14px}
.ans{white-space:pre-wrap;font-size:15px;margin-top:6px}
.kv{font-family:var(--mono);font-size:12.5px;color:var(--muted);margin-top:8px}
.hash{font-family:var(--mono);font-size:11px;color:#5c6b82;word-break:break-all}
.err{color:var(--warn);font-size:13px}
</style></head><body><div class="wrap">
<h1><span class="d">DESi</span> · Reviewer Port</h1>
<p class="sub">Route to a deterministic tool, a local model, or an API model — and see exactly why. Tools run offline; nothing leaves your machine unless an API route is chosen.</p>
<textarea id="q" placeholder="Ask something, or try: what is (9*4)-6 ?"></textarea>
<div class="row">
<div><label>Privacy</label><select id="privacy">
<option value="prefer_local">prefer local</option>
<option value="local_only">local only</option>
<option value="any">any</option></select></div>
<div><label>Accuracy target</label><input id="acc" type="number" step="0.05" min="0" max="1" value="0"/></div>
<div><label>Cost budget $/item</label><input id="cost" type="number" step="0.001" min="0" value="1"/></div>
<div><label>Task class (optional)</label><input id="tc" placeholder="auto-classify"/></div>
</div>
<button onclick="route()">Route</button>
<div id="out"></div>
<div class="card" id="ledger"><div class="k">shared ledger · local Layer 9</div><div class="sub">loading…</div></div>
</div><script>
async function route(){
 const body={query:document.getElementById('q').value,
  privacy:document.getElementById('privacy').value,
  accuracy_target:parseFloat(document.getElementById('acc').value||0),
  cost_budget_usd:parseFloat(document.getElementById('cost').value||1e9),
  task_class:document.getElementById('tc').value||null};
 const out=document.getElementById('out');out.innerHTML='<p class="sub">routing…</p>';
 const r=await fetch('/api/route',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const d=await r.json();const dec=d.decision;
 const cls=dec.locality==='tool'?'tool':(dec.locality==='local'?'local':'api');
 out.innerHTML=`<div class="card">
  <div class="k">decision · ${d.task_class}</div>
  <div class="big ${cls}">${dec.kind.toUpperCase()} → ${dec.target||'—'} <span class="kv">[${dec.locality||'-'}]</span></div>
  <div class="rationale">${dec.rationale}</div>
  <div class="kv">cost ~$${dec.expected_cost_usd} · score ${dec.expected_score==null?'—':dec.expected_score}${dec.below_target?' · ⚠ below target':''}</div>
 </div>
 <div class="card"><div class="k">answer · ${d.answer_source}</div>
  <div class="ans">${d.answer!=null?escapeHtml(d.answer):'<span class="err">'+(d.error||'no answer (model not executed)')+'</span>'}</div></div>
 <div class="card"><div class="k">audit (replay-stable decision hash)</div><div class="hash">${d.audit.decision_hash}</div></div>`;
 loadLedger();
}
function escapeHtml(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
async function loadLedger(){
 const el=document.getElementById('ledger');
 try{
  const d=await(await fetch('/api/ledger')).json();const s=d.stats;
  const rows=d.tail.map(e=>`<div class="kv">#${e.seq} · ${e.instance_id} · ${e.kind} · ${e.payload.task_class||''} · ${e.chain_hash.slice(0,10)}</div>`).join('');
  el.innerHTML=`<div class="k">shared ledger · local Layer 9</div>
   <div class="big ${d.chain_intact?'tool':'api'}">${s.count} events · chain ${d.chain_intact?'intact ✓':'BROKEN ✗'}</div>
   <div class="kv">instances: ${s.instances.join(', ')||'—'}</div>${rows}`;
 }catch(e){el.innerHTML='<div class="k">shared ledger</div><div class="err">unavailable</div>';}
}
document.getElementById('q').addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.metaKey||e.ctrlKey))route();});
loadLedger();
</script></body></html>"""


def _make_handler(registry: Registry, ledger_path: str, instance_id: str):
    tools = default_registry()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, PAGE, "text/html; charset=utf-8")
            elif self.path == "/api/ledger":
                led = Ledger(ledger_path, instance_id=instance_id)
                try:
                    body = {
                        "stats": led.stats(),
                        "chain_intact": led.verify_chain(),
                        "tail": led.tail(8),
                    }
                finally:
                    led.close()
                self._send(200, json.dumps(_json_safe(body)))
            else:
                self._send(404, json.dumps({"error": "not found"}))

        def do_POST(self):
            if self.path != "/api/route":
                self._send(404, json.dumps({"error": "not found"}))
                return
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self._send(400, json.dumps({"error": "bad json"}))
                return
            constraints = Constraints(
                privacy=payload.get("privacy", "prefer_local"),
                cost_budget_usd=float(payload.get("cost_budget_usd", float("inf"))),
                accuracy_target=float(payload.get("accuracy_target", 0.0)),
            )
            led = Ledger(ledger_path, instance_id=instance_id)
            try:
                result = run(
                    payload.get("query", ""),
                    registry=registry,
                    tools=tools,
                    constraints=constraints,
                    task_class=payload.get("task_class") or None,
                    ledger=led,
                )
            finally:
                led.close()
            self._send(200, json.dumps(_json_safe(result)))

        def log_message(self, *args):  # quiet
            pass

    return Handler


def resolve_config(path: str | None) -> Path:
    if path:
        return Path(path)
    local = _HERE / "config.json"
    return local if local.exists() else _HERE / "config.example.json"


def resolve_ledger(path: str | None) -> str:
    if path:
        return path
    return os.environ.get("DESI_LEDGER", str(_HERE / "desi_ledger.db"))


def main() -> None:
    ap = argparse.ArgumentParser(description="DESi Reviewer Port (local router UI)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--config", default=None)
    ap.add_argument("--ledger", default=None, help="shared local-Layer-9 SQLite file")
    args = ap.parse_args()
    cfg = resolve_config(args.config)
    registry = load_config(cfg)
    ledger_path = resolve_ledger(args.ledger)
    instance_id = f"reviewer:{socket.gethostname()}:{args.port}"
    handler = _make_handler(registry, ledger_path, instance_id)
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"DESi Reviewer Port · config={cfg.name} · ledger={Path(ledger_path).name} "
          f"· http://localhost:{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    main()
