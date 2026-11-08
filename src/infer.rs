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
        Ok(Model { model: cfg.model.model.clone(), key: key(cfg), path, recorded })
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
                let r = call(k, &request)?;
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
