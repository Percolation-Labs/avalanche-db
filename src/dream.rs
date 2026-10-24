//! Dreaming turns plain mentions into typed links. Code finds the candidates: every id a
//! note or a commit names. The model judges only what one mention means, as one Choice
//! over the link types that fit those two kinds, plus `only_mentions`. One call per source,
//! so its text is paid for once. Every request is recorded, keyed by its hash, and replayed
//! instead of called, so a recorded dream is offline and deterministic.

use std::collections::BTreeMap;
use std::io::Write;
use std::path::{Path, PathBuf};

use serde_json::{json, Value};
use sha2::{Digest, Sha256};

use crate::config::{Config, DIR};
use crate::model::{FactIn, Kind, Pred};
use crate::store::{ScanCost, Store};
use crate::Result;

pub const ENDPOINT: &str = "https://api.typesafe.ai/v1/systemone";
/// Answers below this probability are kept in the record but written as no link.
pub const ACCEPT: f64 = 0.8;
const ONLY: &str = "only_mentions";
/// Dollars per input token, when a response does not report its own cost.
const PRICE: f64 = 0.042 / 1e6;

/// The link types a mention from `s` to `o` may turn into, with what each means.
fn options(s: Kind, o: Kind, target: &str) -> Vec<(&'static str, String)> {
    let mut v: Vec<(&'static str, String)> = match (s, o) {
        (Kind::Decision, Kind::Issue) => vec![("because", format!("`record` is a decision made because of {target}"))],
        (Kind::Decision, Kind::Proposal) => vec![
            ("rejects", format!("`record` decides against {target}")),
            ("adopts", format!("`record` decides to adopt {target}")),
        ],
        (Kind::Decision, Kind::File) => vec![("decides", format!("`record` decides how {target} must work"))],
        (Kind::Issue, Kind::Issue) => vec![("duplicates", format!("`record` reports the same problem as {target}"))],
        (Kind::Commit, Kind::Issue) => vec![("fixes", format!("`record` is a change that fixes {target}"))],
        (Kind::Commit, Kind::Decision) => vec![("implements", format!("`record` is a change that carries out {target}"))],
        _ => vec![],
    };
    if !v.is_empty() {
        v.push((ONLY, format!("`record` names {target} but none of the above holds")));
    }
    v
}

pub struct Decision {
    pub s: String,
    pub o: String,
    pub choice: String,
    pub p: f64,
}

pub struct Report {
    pub mentions: usize,
    pub sources: BTreeMap<Kind, usize>,
    pub calls: usize,
    pub replayed: usize,
    pub cost: f64,
    pub decisions: Vec<Decision>,
    pub tx: Option<u64>,
    pub written: usize,
}

fn key_file() -> Option<PathBuf> {
    std::env::var_os("HOME").map(|h| PathBuf::from(h).join(".config/avalanche/key"))
}

/// The model key: the configured environment variable, else the user config file.
pub fn key(cfg: &Config) -> Option<String> {
    std::env::var(&cfg.model.key_env).ok().filter(|k| !k.is_empty()).or_else(|| key_file().and_then(|p| std::fs::read_to_string(p).ok()).map(|k| k.trim().to_string()).filter(|k| !k.is_empty()))
}

pub fn set_key(k: &str) -> Result<PathBuf> {
    let p = key_file().ok_or("no HOME")?;
    std::fs::create_dir_all(p.parent().unwrap())?;
    std::fs::write(&p, k.trim())?;
    #[cfg(unix)]
    std::fs::set_permissions(&p, std::os::unix::fs::PermissionsExt::from_mode(0o600))?;
    Ok(p)
}

fn call(key: &str, body: &Value) -> Result<Value> {
    let resp = ureq::post(ENDPOINT).set("Authorization", &format!("Bearer {key}")).send_json(body.clone());
    match resp {
        Ok(r) => Ok(r.into_json()?),
        Err(ureq::Error::Status(code, r)) => Err(format!("{ENDPOINT}: {code} {}", r.into_string().unwrap_or_default()).into()),
        Err(e) => Err(e.into()),
    }
}

pub fn check_key(cfg: &Config) -> Result<String> {
    let k = key(cfg).ok_or_else(|| format!("no key: set {} or run `ava key set`", cfg.model.key_env))?;
    let body = json!({"model": cfg.model.model, "state": {"record": "The sky is blue."},
        "questions": {"q": {"type": "noul", "instructions": "Does `record` describe a colour?"}}});
    let r = call(&k, &body)?;
    Ok(r.get("model").and_then(Value::as_str).unwrap_or(&cfg.model.model).to_string())
}

struct Recorded {
    path: PathBuf,
    entries: BTreeMap<String, Value>,
}

impl Recorded {
    fn open(dir: &Path) -> Result<Recorded> {
        let path = dir.join(DIR).join("decisions.jsonl");
        let mut entries = BTreeMap::new();
        if let Ok(text) = std::fs::read_to_string(&path) {
            for line in text.lines().filter(|l| !l.trim().is_empty()) {
                let v: Value = serde_json::from_str(line)?;
                entries.insert(v["key"].as_str().unwrap_or_default().to_string(), v);
            }
        }
        Ok(Recorded { path, entries })
    }

    fn append(&mut self, key: &str, request: &Value, response: &Value) -> Result<()> {
        let line = json!({"key": key, "request": request, "response": response});
        let mut f = std::fs::OpenOptions::new().create(true).append(true).open(&self.path)?;
        writeln!(f, "{line}")?;
        self.entries.insert(key.to_string(), line);
        Ok(())
    }
}

fn hash(v: &Value) -> String {
    Sha256::digest(v.to_string().as_bytes()).iter().map(|b| format!("{b:02x}")).collect()
}

fn label(store: &Store, t: u32, id: u64, as_of: u64) -> Result<Option<(String, i64)>> {
    for e in store.edges(t, id, crate::store::Dir::Out, as_of, None, &mut ScanCost::default())? {
        if e.pred == Pred::Label {
            return Ok(Some((store.name(t, e.other)?.trim_start_matches("lit:").to_string(), e.valid_from)));
        }
    }
    Ok(None)
}

pub fn dream(store: &Store, t: u32, dir: &Path, cfg: &Config) -> Result<Report> {
    let head = store.head(t)?;
    let mut cost_scan = ScanCost::default();
    let typed: Vec<(u64, u64)> = Pred::ALL
        .iter()
        .filter(|p| options_preds().contains(p))
        .map(|p| store.by_pred(t, *p, head, &mut cost_scan))
        .collect::<Result<Vec<_>>>()?
        .into_iter()
        .flatten()
        .map(|(s, o, _)| (s, o))
        .collect();
    // Candidates grouped by source, in name order, so calls and output are stable.
    let mut by_source: BTreeMap<String, Vec<(String, u64)>> = BTreeMap::new();
    let mut ids: BTreeMap<String, u64> = BTreeMap::new();
    for (s, o, _) in store.by_pred(t, Pred::Mentions, head, &mut cost_scan)? {
        if typed.contains(&(s, o)) {
            continue;
        }
        let (sn, on) = (store.name(t, s)?, store.name(t, o)?);
        if options(Kind::of(&sn).unwrap(), Kind::of(&on).unwrap(), "x").is_empty() {
            continue;
        }
        ids.insert(sn.clone(), s);
        by_source.entry(sn).or_default().push((on, o));
    }
    let mut recorded = Recorded::open(dir)?;
    let key = key(cfg);
    let mut report = Report { mentions: 0, sources: BTreeMap::new(), calls: 0, replayed: 0, cost: 0.0, decisions: vec![], tx: None, written: 0 };
    let mut pending = vec![];
    for (source, targets) in &by_source {
        let sid = ids[source];
        let pointer = store
            .edges(t, sid, crate::store::Dir::Out, head, None, &mut cost_scan)?
            .into_iter()
            .find(|e| e.pred == Pred::Pointer)
            .map(|e| store.name(t, e.other))
            .transpose()?
            .ok_or_else(|| format!("{source} has no pointer to read"))?;
        let text = crate::ingest::content(dir, pointer.trim_start_matches("lit:"))?;
        let sk = Kind::of(source).unwrap();
        *report.sources.entry(sk).or_default() += 1;
        let mut questions = serde_json::Map::new();
        for (i, (target, oid)) in targets.iter().enumerate() {
            let shown = match label(store, t, *oid, head)? {
                Some((l, _)) => format!("{} (\"{l}\")", target.split_once(':').unwrap().1),
                None => target.split_once(':').unwrap().1.to_string(),
            };
            let opts: serde_json::Map<String, Value> = options(sk, Kind::of(target).unwrap(), &shown).into_iter().map(|(k, d)| (k.to_string(), Value::String(d))).collect();
            questions.insert(format!("m{i}"), json!({"type": "choice", "instructions": format!("`record` names {shown}. What is `record`'s link to it?"), "criteria": opts}));
            report.mentions += 1;
        }
        let request = json!({"model": cfg.model.model, "state": {"record": text}, "questions": questions});
        let h = hash(&request);
        let response = match recorded.entries.get(&h) {
            Some(v) => {
                report.replayed += 1;
                v["response"].clone()
            }
            None => {
                let Some(k) = &key else {
                    pending.push(source.clone());
                    continue;
                };
                let r = call(k, &request)?;
                recorded.append(&h, &request, &r)?;
                r
            }
        };
        report.calls += 1;
        let usage = &response["usage"];
        report.cost += usage["cost"].as_f64().unwrap_or_else(|| usage["input_tokens"].as_f64().unwrap_or(0.0) * PRICE);
        for (i, (target, _)) in targets.iter().enumerate() {
            let a = &response["answers"][format!("m{i}")];
            let choice = a["choice"].as_str().unwrap_or(ONLY).to_string();
            let p = a["probabilities"][&choice].as_f64().unwrap_or(0.0);
            report.decisions.push(Decision { s: source.clone(), o: target.clone(), choice, p });
        }
    }
    if !pending.is_empty() {
        return Err(format!("{} sources need the model and no key is set ({}); nothing written. Set {} or run `ava key set`.", pending.len(), pending.join(", "), cfg.model.key_env).into());
    }
    let mut facts = vec![];
    for d in &report.decisions {
        if d.choice == ONLY || d.p < ACCEPT {
            continue;
        }
        let at = label(store, t, ids[&d.s], head)?.map(|(_, at)| at);
        let mut f = FactIn::new(&d.s, Pred::from_name(&d.choice).ok_or_else(|| format!("{}: not a link type", d.choice))?, &d.o, "dream");
        f.valid_from = at;
        facts.push(f);
    }
    if !facts.is_empty() {
        report.written = facts.len();
        report.tx = Some(store.write(t, &facts)?);
    }
    Ok(report)
}

/// The link types dreaming writes; a mention already turned into one is not asked again.
fn options_preds() -> Vec<Pred> {
    vec![Pred::Because, Pred::Rejects, Pred::Adopts, Pred::Decides, Pred::Duplicates, Pred::Fixes, Pred::Implements]
}
