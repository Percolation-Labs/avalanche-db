//! `avalanche.toml`: what to read, which kind of thing an id names, and which model may
//! read it. `ava init` writes it from what it finds in the folder.

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::Result;

pub const FILE: &str = "avalanche.toml";
pub const DIR: &str = ".avalanche";

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Config {
    pub tenant: String,
    #[serde(default, rename = "source")]
    pub sources: Vec<SourceCfg>,
    /// Id prefix (`ADR` in `ADR-007`) to the kind of thing it names.
    #[serde(default)]
    pub ids: BTreeMap<String, String>,
    #[serde(default)]
    pub model: ModelCfg,
    /// Named paths for P8QL: hops with the kinds between them, ending with an arrow.
    #[serde(default = "default_paths")]
    pub paths: BTreeMap<String, String>,
}

/// The paths every store starts with; `[paths]` in avalanche.toml replaces them.
pub fn default_paths() -> BTreeMap<String, String> {
    BTreeMap::from([("works_with".to_string(), "<-authoredBy- commit -touches-> file <-touches- commit -authoredBy->".to_string())])
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SourceCfg {
    pub adapter: String,
    /// A folder, or a git repository for `git` and for `markdown` read at a revision.
    #[serde(default)]
    pub path: PathBuf,
    /// Read a git source at this revision instead of the working tree (`origin/main`).
    #[serde(default)]
    pub rev: Option<String>,
    /// For `markdown` at a revision: the folder inside the repository.
    #[serde(default)]
    pub dir: Option<String>,
    /// For `github`: owner/name.
    #[serde(default)]
    pub repo: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ModelCfg {
    pub provider: String,
    pub model: String,
    pub key_env: String,
}

impl Default for ModelCfg {
    fn default() -> Self {
        ModelCfg { provider: "jev".into(), model: "jev-1.13.0".into(), key_env: "AVALANCHE_MODEL_KEY".into() }
    }
}

impl Config {
    pub fn load(dir: &Path) -> Result<Config> {
        let path = dir.join(FILE);
        let text = std::fs::read_to_string(&path).map_err(|e| format!("{}: {e} (run `ava init` first)", path.display()))?;
        Ok(toml::from_str(&text).map_err(|e| format!("{}: {e}", path.display()))?)
    }

    pub fn store_path(dir: &Path) -> PathBuf {
        dir.join(DIR).join("store.redb")
    }

    /// The node an id names (`ADR-007` -> `decision:ADR-007`), if its prefix is known.
    pub fn node_for_id(&self, id: &str) -> Option<String> {
        let (prefix, n) = id.split_once('-')?;
        if n.is_empty() || !n.bytes().all(|b| b.is_ascii_digit()) {
            return None;
        }
        let kind = crate::model::Kind::prefix(self.ids.get(prefix)?)?;
        Some(format!("{kind}:{id}"))
    }

    /// Every `PREFIX-123` in a text whose prefix the table knows, in order, once each.
    /// Branch names write ids in lower case (`amartey/rem-1160-…`), so case is ignored.
    pub fn ids_in(&self, text: &str) -> Vec<String> {
        let mut out = vec![];
        let upper = text.to_uppercase();
        for word in upper.split(|c: char| !(c.is_ascii_alphanumeric() || c == '-')) {
            for part in id_parts(word) {
                if let Some(node) = self.node_for_id(part) {
                    if !out.contains(&node) {
                        out.push(node);
                    }
                }
            }
        }
        out
    }

    /// Look at a folder and propose a config: a git repository at `.` or one level down,
    /// note folders holding markdown with frontmatter, and the id prefixes those notes use.
    pub fn discover(dir: &Path) -> Result<Config> {
        let mut sources = vec![];
        let mut ids = BTreeMap::new();
        let mut entries: Vec<PathBuf> = std::fs::read_dir(dir)?.filter_map(|e| e.ok().map(|e| e.path())).collect();
        entries.sort();
        if dir.join(".git").exists() {
            sources.push(SourceCfg { adapter: "git".into(), path: ".".into(), rev: None, dir: None, repo: None });
        }
        for p in &entries {
            let name = p.file_name().unwrap().to_string_lossy().into_owned();
            if !p.is_dir() || name.starts_with('.') {
                continue;
            }
            if p.join(".git").exists() {
                sources.push(SourceCfg { adapter: "git".into(), path: name.clone().into(), rev: None, dir: None, repo: None });
                continue;
            }
            let notes = crate::construct::ingest::notes_in(p)?;
            if notes.is_empty() {
                continue;
            }
            for n in &notes {
                if let (Some(id), Some(kind)) = (&n.id, &n.kind) {
                    if let Some((prefix, _)) = id.split_once('-') {
                        ids.insert(prefix.to_string(), kind.clone());
                    }
                }
            }
            sources.push(SourceCfg { adapter: "markdown".into(), path: name.into(), rev: None, dir: None, repo: None });
        }
        for p in &entries {
            let is_export = p.extension().is_some_and(|x| x == "json")
                && std::fs::read_to_string(p).ok().and_then(|t| serde_json::from_str::<serde_json::Value>(&t).ok()).is_some_and(|v| v["packages"].is_array());
            if is_export {
                sources.push(SourceCfg { adapter: "percolate".into(), path: p.file_name().unwrap().into(), rev: None, dir: None, repo: None });
            }
        }
        Ok(Config { tenant: "me".into(), sources, ids, model: ModelCfg::default(), paths: default_paths() })
    }

    pub fn to_toml(&self) -> String {
        let mut s = format!("tenant = \"{}\"\n", self.tenant);
        for src in &self.sources {
            s += &format!("\n[[source]]\nadapter = \"{}\"\npath = \"{}\"\n", src.adapter, src.path.display());
        }
        s += "\n[ids]\n";
        for (k, v) in &self.ids {
            s += &format!("{k} = \"{v}\"\n");
        }
        s += "\n[paths]                  # named paths for P8QL queries: hops, and the kinds between them\n";
        for (k, v) in &self.paths {
            s += &format!("{k} = \"{v}\"\n");
        }
        s += &format!("\n[model]\nprovider = \"{}\"\nmodel = \"{}\"\nkey_env = \"{}\"\n", self.model.provider, self.model.model, self.model.key_env);
        s
    }
}

/// The `PREFIX-123` ids inside one hyphenated word: `REM-1160-DRY-RUN` holds `REM-1160`.
fn id_parts(word: &str) -> Vec<&str> {
    let mut out = vec![];
    let bytes = word.as_bytes();
    let mut start = 0;
    for (i, b) in bytes.iter().enumerate() {
        if *b == b'-' && i > start && bytes[start..i].iter().all(|c| c.is_ascii_uppercase()) {
            let digits = bytes[i + 1..].iter().take_while(|c| c.is_ascii_digit()).count();
            let end = i + 1 + digits;
            if digits > 0 && (end == bytes.len() || bytes[end] == b'-') {
                out.push(&word[start..end]);
            }
        }
        if *b == b'-' {
            start = i + 1;
        }
    }
    out
}
