"""standin.py -- the Jev stand-in: Qwen3-Reranker-0.6B, local, spends no tokens.

The team's measured stand-in for Jev (p8-subsystems meta/lab/results/jev-standin, PR #617: Spearman
.683 with Jev, AUC .924 on Jev's accepts). It reads a query, an instruction and a document, and
gives P(yes), so it answers a Noul. A Choice is one Noul per option, and the best one wins. The
template is the model card's, as in bill's standin.py. Scores are cached by their exact input in
.waves/standin.jsonl, so a rerun reads the cache.

Needs torch and transformers; the weights come from Hugging Face on first use (HF_HOME decides where).
"""
import hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".waves", "standin.jsonl")
NAME = "Qwen/Qwen3-Reranker-0.6B"
_model = None
_cache = None


def _load():
    global _model
    if _model is None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        dev = "mps" if torch.backends.mps.is_available() else "cpu"
        tok = AutoTokenizer.from_pretrained(NAME, padding_side="left")
        model = AutoModelForCausalLM.from_pretrained(NAME, dtype=torch.float16).to(dev).eval()
        prefix = ("<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the "
                  "Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n")
        suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        _model = (torch, tok, model, dev, tok.encode(prefix, add_special_tokens=False),
                  tok.encode(suffix, add_special_tokens=False),
                  tok.convert_tokens_to_ids("yes"), tok.convert_tokens_to_ids("no"))
    return _model


def nouls(query, instruct, docs, maxlen=1024):
    """P(yes) for each document."""
    global _cache
    if _cache is None:
        _cache = {}
        if os.path.exists(CACHE):
            for line in open(CACHE):
                d = json.loads(line)
                _cache[d["key"]] = d["p"]
    keys = [hashlib.sha256(json.dumps([NAME, query, instruct, d]).encode()).hexdigest() for d in docs]
    todo = [i for i, k in enumerate(keys) if k not in _cache]
    if todo:
        torch, tok, model, dev, pre, suf, yes, no = _load()
        bodies = [f"<Instruct>: {instruct}\n<Query>: {query}\n<Document>: {docs[i]}" for i in todo]
        enc = tok(bodies, padding=False, truncation="longest_first", return_attention_mask=False,
                  max_length=maxlen - len(pre) - len(suf), add_special_tokens=False)
        batch = tok.pad({"input_ids": [pre + x + suf for x in enc["input_ids"]]}, padding=True, return_tensors="pt").to(dev)
        with torch.no_grad():
            logits = model(**batch).logits[:, -1, :]
        p = torch.softmax(torch.stack([logits[:, no], logits[:, yes]], dim=1).float(), dim=1)[:, 1].cpu().tolist()
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "a") as f:
            for i, v in zip(todo, p):
                _cache[keys[i]] = v
                f.write(json.dumps({"key": keys[i], "p": v}) + "\n")
    return [_cache[k] for k in keys]


def choice(query, instruct, options):
    """A Choice as one Noul per option: (best key, {key: p})."""
    ks = list(options)
    ps = nouls(query, instruct, [options[k] for k in ks])
    scored = dict(zip(ks, ps))
    return max(scored, key=scored.get), scored
