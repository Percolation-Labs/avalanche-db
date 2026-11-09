//! INFER: the only place a model is called. A request is a state and typed questions; the
//! answer is a choice with a probability, nothing generated. Every request is recorded,
//! keyed by the hash of its exact body, and replayed instead of called, so anything built
//! on a recording is offline and deterministic. The walk never comes here.

use std::collections::BTreeMap;
use std::io::Write;
use std::path::{Path, PathBuf};

use serde_json::{json, Value};
use sha2::{Digest, Sha256};

use crate::config::{Config, DIR};
use crate::Result;

pub const ENDPOINT: &str = "https://api.typesafe.ai/v1/systemone";
/// Dollars per input token, when a response does not report its own cost.
const PRICE: f64 = 0.042 / 1e6;

fn key_file() -> Option<PathBuf> {
    std::env::var_os("HOME").map(|h| PathBuf::from(h).join(".config/avalanche/key"))
}

/// The model key: the configured environment variable, else the user config file.
pub fn key(cfg: &Config) -> Option<String> {
    std::env::var(&cfg.model.key_env)
        .ok()
        .filter(|k| !k.is_empty())
        .or_else(|| key_file().and_then(|p| std::fs::read_to_string(p).ok()).map(|k| k.trim().to_string()).filter(|k| !k.is_empty()))
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
    match ureq::post(ENDPOINT).set("Authorization", &format!("Bearer {key}")).send_json(body.clone()) {
        Ok(r) => Ok(r.into_json()?),
        Err(ureq::Error::Status(code, r)) => Err(format!("{ENDPOINT}: {code} {}", r.into_string().unwrap_or_default()).into()),
        Err(e) => Err(e.into()),
    }
}

/// The stand-in decider (provider = "claude"): the same typed questions, answered by
/// `claude -p` on the subscription, for when the decision model has no credit. Its
/// probabilities are the model's own report, not a calibrated score, and its answers are
/// recorded under its own model name, so they never replay as the decision model's.
fn call_claude(model: &str, body: &Value) -> Result<Value> {
    let mut prompt = String::from("You decide typed questions about one record. Answer each question by choosing exactly one of its options, and give the probability you put on that choice (0 to 1). Reply with JSON only, no prose: {\"<question id>\": {\"choice\": \"<option>\", \"p\": <number>}, ...}\n\nRecord:\n");
    prompt += body["state"]["record"].as_str().unwrap_or_default();
    prompt += "\n\nQuestions:\n";
    if let Some(qs) = body["questions"].as_object() {
        for (id, q) in qs {
            prompt += &format!("\n{id}: {}\n", q["instructions"].as_str().unwrap_or_default());
            if let Some(opts) = q["criteria"].as_object() {
                for (k, d) in opts {
                    prompt += &format!("  - {k}: {}\n", d.as_str().unwrap_or_default());
                }
            }
        }
    }
    // stream-json, because a user's Stop hook can add a turn after the answer: the answer is
    // the first assistant text that parses as a JSON object naming the questions.
    let out = std::process::Command::new("claude")
        .args(["-p", &prompt, "--model", model.strip_prefix("claude:").unwrap_or(model), "--output-format", "stream-json", "--verbose", "--tools", "", "--strict-mcp-config", "--no-session-persistence"])
        .output()?;
    if !out.status.success() {
        return Err(format!("claude -p failed: {}", String::from_utf8_lossy(&out.stderr)).into());
    }
    let ids: Vec<String> = body["questions"].as_object().map(|m| m.keys().cloned().collect()).unwrap_or_default();
    let mut got: Option<Value> = None;
    let mut cost = Value::Null;
    for line in String::from_utf8_lossy(&out.stdout).lines() {
        let Ok(ev) = serde_json::from_str::<Value>(line) else { continue };
        if ev["type"] == "result" {
            cost = ev["total_cost_usd"].clone();
        }
        if got.is_some() || ev["type"] != "assistant" {
            continue;
        }
        for part in ev["message"]["content"].as_array().into_iter().flatten() {
            let text = part["text"].as_str().unwrap_or_default();
            let Some(t) = text.find('{').and_then(|a| text.rfind('}').map(|b| &text[a..=b])) else { continue };
            if let Ok(v) = serde_json::from_str::<Value>(t) {
                if ids.iter().any(|id| v.get(id).is_some()) {
                    got = Some(v);
                    break;
                }
            }
        }
    }
    let got = got.ok_or("the stand-in gave no answer that names the questions")?;
    let mut answers = serde_json::Map::new();
    if let Some(m) = got.as_object() {
        for (id, a) in m {
            let choice = a["choice"].as_str().unwrap_or_default().to_string();
            let p = a["p"].as_f64().unwrap_or(0.0);
            answers.insert(id.clone(), json!({"choice": choice, "probabilities": {choice.clone(): p}}));
        }
    }
    Ok(json!({"answers": answers, "usage": {"cost": 0.0}, "stand_in": cost}))
}

pub fn check_key(cfg: &Config) -> Result<String> {
    let k = key(cfg).ok_or_else(|| format!("no key: set {} or run `midb key set`", cfg.model.key_env))?;
    let body = json!({"model": cfg.model.model, "state": {"record": "The sky is blue."},
        "questions": {"q": {"type": "noul", "instructions": "Does `record` describe a colour?"}}});
    let r = call(&k, &body)?;
    Ok(r.get("model").and_then(Value::as_str).unwrap_or(&cfg.model.model).to_string())
}

/// One typed question: a Choice over named options, each with what it means.
pub struct Choice {
    pub instructions: String,
    pub options: Vec<(String, String)>,
}

/// One answer: the option chosen and its probability.
pub struct Answer {
    pub choice: String,
    pub p: f64,
}

pub enum Outcome {
    Answered { answers: Vec<Answer>, replayed: bool, cost: f64 },
    /// Not recorded, and no key to call with.
    NeedsKey,
}

/// The decision model behind a recording.
pub struct Model {
    model: String,
    provider: String,
    key: Option<String>,
    path: PathBuf,
    recorded: BTreeMap<String, Value>,
}

impl Model {
    pub fn open(dir: &Path, cfg: &Config) -> Result<Model> {
        let path = dir.join(DIR).join("decisions.jsonl");
        let mut recorded = BTreeMap::new();
        if let Ok(text) = std::fs::read_to_string(&path) {
            for line in text.lines().filter(|l| !l.trim().is_empty()) {
                let v: Value = serde_json::from_str(line)?;
                recorded.insert(v["key"].as_str().unwrap_or_default().to_string(), v);
            }
        }
        let key = if cfg.model.provider == "claude" { Some("subscription".into()) } else { key(cfg) };
        Ok(Model { model: cfg.model.model.clone(), provider: cfg.model.provider.clone(), key, path, recorded })
    }

    fn request(&self, state: &str, questions: &[Choice]) -> (Value, String) {
        let qs: serde_json::Map<String, Value> = questions
            .iter()
            .enumerate()
            .map(|(i, q)| {
                let opts: serde_json::Map<String, Value> = q.options.iter().map(|(k, d)| (k.clone(), Value::String(d.clone()))).collect();
                (format!("m{i}"), json!({"type": "choice", "instructions": q.instructions, "criteria": opts}))
            })
            .collect();
        let request = json!({"model": self.model, "state": {"record": state}, "questions": qs});
        let h: String = Sha256::digest(request.to_string().as_bytes()).iter().map(|b| format!("{b:02x}")).collect();
        (request, h)
    }

    /// What one request would cost before it is sent: (recorded already, estimated dollars).
    /// Input tokens are estimated at three characters each: on the percolate history four
    /// under-counted by a third ($0.086 estimated, $0.125 billed).
    pub fn estimate(&self, state: &str, questions: &[Choice]) -> (bool, f64) {
        let (request, h) = self.request(state, questions);
        (self.recorded.contains_key(&h), request.to_string().len() as f64 / 3.0 * PRICE)
    }

    /// Ask every question about one state in one request: the state is paid for once.
    pub fn ask(&mut self, state: &str, questions: &[Choice]) -> Result<Outcome> {
        let (request, h) = self.request(state, questions);
        let (response, replayed) = match self.recorded.get(&h) {
            Some(v) => (v["response"].clone(), true),
            None => {
                let Some(k) = &self.key else { return Ok(Outcome::NeedsKey) };
                let r = if self.provider == "claude" { call_claude(&self.model, &request)? } else { call(k, &request)? };
                let line = json!({"key": h, "request": request, "response": r});
                let mut f = std::fs::OpenOptions::new().create(true).append(true).open(&self.path)?;
                writeln!(f, "{line}")?;
                self.recorded.insert(h, line);
                (r, false)
            }
        };
        let usage = &response["usage"];
        let cost = usage["cost"].as_f64().unwrap_or_else(|| usage["input_tokens"].as_f64().unwrap_or(0.0) * PRICE);
        let answers = (0..questions.len())
            .map(|i| {
                let a = &response["answers"][format!("m{i}")];
                let choice = a["choice"].as_str().unwrap_or_default().to_string();
                let p = a["probabilities"][&choice].as_f64().unwrap_or(0.0);
                Answer { choice, p }
            })
            .collect();
        Ok(Outcome::Answered { answers, replayed, cost })
    }
}
