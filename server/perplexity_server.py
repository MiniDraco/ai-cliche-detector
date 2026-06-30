"""
Local detection backend for the AI detector suite. Computes the signals
stylometry can't:

  * Perplexity + burstiness + GLTR-style rank metrics (single observer model)
  * BINOCULARS score (Hans et al. 2024) -- the SOTA zero-shot method: the ratio
    of a text's log-perplexity under an OBSERVER model to its cross-perplexity
    between the observer and a PERFORMER model. The cross-perplexity normalization
    cancels prompt/domain effects, so it works far better than raw perplexity
    (esp. on high-perplexity domains like song lyrics). Lower Binoculars = AI.

Runs on stdlib http.server (no fastapi/flask). Launch with a python that already
has torch+transformers (e.g. the ComfyUI embedded python) -- nothing is installed.

  POST /score  {"text": "..."} -> {perplexity, mean_bits, burstiness_bits,
                                   mean_rank, pct_top1, pct_top10,
                                   binoculars, log_ppl, log_xppl, tokens, ...}
  GET  /health                 -> {ok, observer, performer, device, loaded}
"""
import json, math, os, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModel

OBSERVER = os.environ.get("PPL_OBSERVER", os.environ.get("PPL_MODEL", "gpt2"))
PERFORMER = os.environ.get("PPL_PERFORMER", "distilgpt2")   # must share the observer's vocab
EMB_MODEL = os.environ.get("PPL_EMBED", "sentence-transformers/all-MiniLM-L6-v2")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAXLEN = int(os.environ.get("PPL_MAXLEN", "1024"))
_tok = None
_obs = None
_perf = None
_emb_tok = None
_emb = None


def load():
    global _tok, _obs, _perf
    if _obs is None:
        _tok = AutoTokenizer.from_pretrained(OBSERVER)
        _obs = AutoModelForCausalLM.from_pretrained(OBSERVER).to(DEVICE).eval()
        _perf = AutoModelForCausalLM.from_pretrained(PERFORMER).to(DEVICE).eval()
    return _tok, _obs, _perf


def load_emb():
    global _emb_tok, _emb
    if _emb is None:
        _emb_tok = AutoTokenizer.from_pretrained(EMB_MODEL)
        _emb = AutoModel.from_pretrained(EMB_MODEL).to(DEVICE).eval()
    return _emb_tok, _emb


@torch.no_grad()
def coherence(text):
    # semantic coherence: do lines develop a connected thread, or jump between disconnected vibes?
    lines = [l.strip() for l in text.split("\n")
             if l.strip() and not re.match(r"^\s*[\[(].*[\])]\s*$", l)]
    if len(lines) < 3:
        return None
    tok, model = load_emb()
    enc = tok(lines, padding=True, truncation=True, max_length=64, return_tensors="pt").to(DEVICE)
    out = model(**enc).last_hidden_state
    mask = enc["attention_mask"].unsqueeze(-1).float()
    emb = (out * mask).sum(1) / mask.sum(1).clamp(min=1e-9)   # mean pooling
    emb = F.normalize(emb, dim=-1)
    adj = (emb[:-1] * emb[1:]).sum(-1)                        # cosine between consecutive lines
    centroid = F.normalize(emb.mean(0, keepdim=True), dim=-1)
    centro = (emb * centroid).sum(-1)                        # how tightly lines cluster on one theme
    return {
        "coh_adjacent": float(adj.mean().item()),
        "coh_adjacent_std": float(adj.std().item()) if adj.numel() > 1 else 0.0,
        "coh_centroid": float(centro.mean().item()),
        "coh_lines": len(lines),
    }


@torch.no_grad()
def score(text):
    tok, obs, perf = load()
    ids = tok(text, return_tensors="pt", truncation=True, max_length=MAXLEN).input_ids.to(DEVICE)
    if ids.shape[1] < 2:
        return None
    lab = ids[:, 1:]
    lo = obs(ids).logits[:, :-1, :]        # observer logits
    lp = perf(ids).logits[:, :-1, :]       # performer logits (same tokenization)

    logp_o = F.log_softmax(lo, dim=-1)
    tok_lp = logp_o.gather(-1, lab.unsqueeze(-1)).squeeze(-1)[0]     # nat log-prob of true tokens
    nll = -tok_lp                                                    # surprisal per token (nats)
    bits = nll / math.log(2)
    log_ppl = float(nll.mean().item())                              # observer log-perplexity (nats)

    # cross-perplexity: H(P_observer, P_performer) per position, averaged
    p_o = F.softmax(lo, dim=-1)
    logp_p = F.log_softmax(lp, dim=-1)
    xent = -(p_o * logp_p).sum(-1)[0]                               # per-position cross entropy (nats)
    log_xppl = float(xent.mean().item())
    binoculars = (log_ppl / log_xppl) if log_xppl > 1e-9 else 0.0

    # GLTR-style rank metrics from the observer
    gathered = lo.gather(-1, lab.unsqueeze(-1))
    ranks = (lo > gathered).sum(-1)[0]
    out = {
        "perplexity": math.exp(log_ppl),
        "mean_bits": float(bits.mean().item()),
        "burstiness_bits": float(bits.std().item()) if bits.numel() > 1 else 0.0,
        "mean_rank": float(ranks.float().mean().item()),
        "pct_top1": float((ranks == 0).float().mean().item()),
        "pct_top10": float((ranks < 10).float().mean().item()),
        "binoculars": binoculars,
        "log_ppl": log_ppl,
        "log_xppl": log_xppl,
        "tokens": int(ids.shape[1]),
        "device": DEVICE,
        "observer": OBSERVER,
        "performer": PERFORMER,
    }
    coh = coherence(text)
    if coh:
        out.update(coh)
    return out


class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/health"):
            self._json(200, {"ok": True, "observer": OBSERVER, "performer": PERFORMER,
                             "device": DEVICE, "loaded": _obs is not None})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            text = (data.get("text") or "").strip()
            res = score(text) if text else None
            self._json(200 if res else 400, res or {"error": "text too short"})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PPL_PORT", "8770"))
    print(f"[detect] observer={OBSERVER} performer={PERFORMER} device={DEVICE} port={port}", flush=True)
    print("[detect] loading models (first run downloads them)...", flush=True)
    load()
    load_emb()
    print(f"[detect] ready on http://127.0.0.1:{port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
