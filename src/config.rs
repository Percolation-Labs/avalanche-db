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
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SourceCfg {
    pub adapter: String,
    pub path: PathBuf,
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
    pub fn ids_in(&self, text: &str) -> Vec<String> {
        let mut out = vec![];
        for word in text.split(|c: char| !(c.is_ascii_alphanumeric() || c == '-')) {
            if let Some(node) = self.node_for_id(word.trim_matches('-')) {
                if !out.contains(&node) {
                    out.push(node);
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
            sources.push(SourceCfg { adapter: "git".into(), path: ".".into() });
        }
        for p in &entries {
            let name = p.file_name().unwrap().to_string_lossy().into_owned();
            if !p.is_dir() || name.starts_with('.') {
                continue;
            }
            if p.join(".git").exists() {
                sources.push(SourceCfg { adapter: "git".into(), path: name.clone().into() });
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
            sources.push(SourceCfg { adapter: "markdown".into(), path: name.into() });
        }
        Ok(Config { tenant: "me".into(), sources, ids, model: ModelCfg::default() })
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
        s += &format!("\n[model]\nprovider = \"{}\"\nmodel = \"{}\"\nkey_env = \"{}\"\n", self.model.provider, self.model.model, self.model.key_env);
        s
    }
}
