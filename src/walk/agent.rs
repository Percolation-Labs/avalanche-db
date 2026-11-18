//! THE WALK AN AGENT CALLS: a question in, documents out, each with where its content lives and how the walk
//! reached it. `midb walk` and the MCP `walk` tool are this function.
//!
//! The caller's `budget` is k, the documents returned. Full-text search picks the first `seeds` (s, ceil(k/2) by
//! default); the walk then
//! fills the other k - s through doors: each wave the doors raised so far are described from the graph alone
//! (`describe`, D6), ranked by Jev in one batch (`jev`), and the best one is opened and read, until k documents are
//! read. Search reads again only when no door is open. With no key the doors are ranked by search's order instead,
//! and the result says so. `reads` is the lab's operator a instead (10 seeds, waves of 50 filled by search, one
//! door a wave, stop at `reads`), the shape the lab's a-k1 walks were recorded in.
//!
//! `Corpus` says where the documents and their doors are: the folder's own store, whose `documents` source wrote
//! passages with their doors at ingestion (labelled by D6, ordered by full-text search), or a lab-imported
//! conversation (labelled as the lab's `describe.lines`, so a walk can be held to the lab's). `content` reads a
//! document from where it lives: ingestion's `documents::Reader`, or the lab's docs.jsonl.

use std::path::{Path, PathBuf};

use serde::Serialize;

use super::d6::D6;
use super::describe::{self, Describe, Docs};
use super::doors::{Decider, DoorLabeller, SearchOrder};
use super::jev::{JevDecider, Kappa, WaveCost};
use super::lab::{self, Graph, Settings};
use super::search;
use super::text::FullText;
use crate::construct::documents::Reader;
use crate::config::{Config, FILE};
use crate::infer::Model;
use crate::model::{short, Pred};
use crate::store::Store;
use crate::Result;

/// Where the walk's documents and doors are.
#[derive(Clone, Debug)]
pub enum Corpus {
    /// The folder's own store: the passages a `documents` source wrote at ingestion, with their doors.
    Project,
    /// A lab-imported conversation (`midb lab import`), with the docs.jsonl its documents' text is in.
    Lab { store: PathBuf, conv: String, docs: Option<PathBuf> },
}

#[derive(Clone, Debug)]
pub struct Opts {
    /// k: how many documents the walk returns.
    pub budget: usize,
    /// s: how many of them full-text search picks before the walk follows doors: ceil(k/2) by default, bill's k-mode
    /// sweep (best at k = 5, 10 and 20 on MuSiQue and p8); under `reads`, 10.
    pub seeds: Option<usize>,
    /// Operator a, for holding a walk to the lab's recorded ones: waves of 50 filled by search, stop at this many.
    pub reads: Option<usize>,
    /// Search's order supplied by the caller (to hold a walk to a recorded one); none: the store's own search.
    pub order: Option<Vec<String>>,
    /// The walk's past (K6) in Jev's state as `found` (kappa round 3); off is the control.
    pub kappa: bool,
    /// How Jev's options are named: F2, as measured, or c{j}, the lab's jevcache (for holding a walk to an a-k1 one).
    pub keys: super::jev::Keys,
    /// Add the walk's full log to the result (`trace`): every wave's batch, every door raised and every read.
    pub trace: bool,
}

impl Default for Opts {
    fn default() -> Opts {
        Opts { budget: 10, seeds: None, reads: None, order: None, kappa: true, keys: super::jev::Keys::F2, trace: false }
    }
}

/// One document the walk read, in reading order.
#[derive(Clone, Debug, Serialize)]
pub struct Found {
    pub rank: usize,
    pub id: String,
    pub label: String,
    /// Where the content lives: a path, `git:`, `jsonl:<file>#<id>`, ...; `read_document` reads it.
    pub location: Option<String>,
    /// `search`, or the key of the door it came through.
    pub via: String,
    pub wave: u32,
}

#[derive(Clone, Debug, Serialize)]
pub struct WaveLog {
    pub wave: u32,
    pub doors: usize,
    pub opened: Vec<String>,
    #[serde(flatten)]
    pub cost: Option<WaveCost>,
}

#[derive(Clone, Debug, Serialize)]
pub struct AgentWalk {
    pub question: String,
    pub decider: String,
    pub note: Option<String>,
    pub budget: usize,
    pub seeds: usize,
    pub documents: Vec<Found>,
    pub waves: Vec<WaveLog>,
    pub requests: usize,
    pub replayed: usize,
    pub called: usize,
    pub input_tokens: u64,
    pub cost_usd: f64,
    pub keys_read: u64,
    /// Seconds per phase: `open` (the store and its graph), `search` (search's order), `walk` (the waves).
    pub seconds: std::collections::BTreeMap<String, f64>,
    /// With `Opts.trace`: the walk's own log, for studying it (never shown to a decider).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub trace: Option<Trace>,
}

/// The walk's log: each wave's batch as the decider saw and ranked it, every door raised (with the document that
/// raised it, its wave and its score), and every read in order.
#[derive(Clone, Debug, Serialize)]
pub struct Trace {
    pub batches: Vec<super::doors::BatchLog>,
    pub doors: Vec<lab::Clue>,
    pub reads: Vec<lab::Read>,
}

fn config(dir: &Path) -> Result<Config> {
    if dir.join(FILE).exists() {
        return Config::load(dir);
    }
    Ok(Config { tenant: "me".into(), sources: vec![], ids: Default::default(), model: Default::default(), paths: crate::config::default_paths() })
}

/// A lab document's location: `lab:<docs.jsonl>#<uri>`.
fn lab_pointer(docs: &Path, id: &str) -> String {
    let p = std::fs::canonicalize(docs).unwrap_or_else(|_| docs.to_path_buf());
    format!("lab:{}#{id}", p.display())
}

pub fn walk(dir: &Path, corpus: &Corpus, question: &str, o: &Opts) -> Result<AgentWalk> {
    if o.budget == 0 || o.reads == Some(0) {
        return Err("a walk returns at least 1 document".into());
    }
    match corpus {
        Corpus::Project => project_walk(dir, question, o),
        Corpus::Lab { store, conv, docs } => lab_walk(dir, store, conv, docs.as_deref(), question, o),
    }
}

const NO_DOCUMENTS: &str = "no documents in this store yet: ingest the folder first (the MCP tool ingest_repo, or add a \
`documents` source with path \".\" to avalanche.toml and run `midb ingest`)";

fn open_project(dir: &Path) -> Result<(Store, u32)> {
    if !dir.join(FILE).exists() {
        return Err(NO_DOCUMENTS.into());
    }
    let cfg = Config::load(dir)?;
    let store = Store::open(Config::store_path(dir))?;
    let t = store.tenant(&cfg.tenant)?;
    Ok((store, t))
}

/// The full-text index of a store at its head, built once per process: an MCP server walks many questions, and on
/// a large store the build (reading every passage back) is most of a walk's time.
fn full_text(dir: &Path, store: &Store, t: u32, g: &mut Graph) -> Result<std::sync::Arc<FullText>> {
    use std::sync::{Arc, Mutex, OnceLock};
    static CACHE: OnceLock<Mutex<Option<(PathBuf, u64, Arc<FullText>)>>> = OnceLock::new();
    let key = (std::fs::canonicalize(dir).unwrap_or_else(|_| dir.to_path_buf()), store.head(t)?);
    let cache = CACHE.get_or_init(|| Mutex::new(None));
    if let Some((d, h, ft)) = cache.lock().unwrap().as_ref() {
        if (d, *h) == (&key.0, key.1) {
            return Ok(ft.clone());
        }
    }
    let ft = Arc::new(FullText::open(dir, t, key.1, g)?);
    *cache.lock().unwrap() = Some((key.0, key.1, ft.clone()));
    Ok(ft)
}

/// The folder's passages, their D6 doors, and full-text search for the seeds and search's order.
fn project_walk(dir: &Path, question: &str, o: &Opts) -> Result<AgentWalk> {
    let clock = std::time::Instant::now();
    let (store, t) = open_project(dir)?;
    let mut g = Graph::open_items(&store, t).map_err(|_| NO_DOCUMENTS)?;
    let opened = clock.elapsed().as_secs_f64();
    let order = match &o.order {
        Some(v) => v.clone(),
        None => full_text(dir, &store, t, &mut g)?.search(question).into_iter().map(|(d, _)| d).collect(),
    };
    if order.is_empty() {
        return Err("no passage shares a word with the question".into());
    }
    let searched = clock.elapsed().as_secs_f64();
    let mut d6 = D6::new(dir);
    let kappa: Option<Kappa> = if o.kappa {
        let mut kg = Graph::open_items(&store, t)?;
        let mut reader = Reader::new(dir);
        Some(Box::new(move |reads: &[lab::Read]| super::kappa::k6(reads, &mut kg, &mut reader)))
    } else {
        None
    };
    let mut w = run(dir, &mut g, order, &mut d6, question, o, kappa)?;
    w.seconds.insert("open".into(), opened);
    w.seconds.insert("search".into(), searched - opened);
    w.seconds.insert("walk".into(), clock.elapsed().as_secs_f64() - searched);
    for d in w.documents.iter_mut() {
        d.label = g.values(&d.id, Pred::Label)?.into_iter().next().unwrap_or_else(|| d.id.clone());
        d.location = g.values(&d.id, Pred::Pointer)?.into_iter().next().map(|p| location(&d.id, &p));
    }
    Ok(w)
}

fn lab_walk(dir: &Path, store: &Path, conv: &str, docs_path: Option<&Path>, question: &str, o: &Opts) -> Result<AgentWalk> {
    if !store.exists() {
        return Err(format!("{}: no such store", store.display()).into());
    }
    let s = Store::open(store)?;
    let mut g = Graph::open(&s, conv)?;
    let docs: Docs = match docs_path {
        Some(p) => describe::load(p)?,
        None => Docs::new(),
    };
    let order = match &o.order {
        Some(v) => v.clone(),
        None => {
            if docs.is_empty() {
                return Err("a lab walk needs the documents' text (--docs) or search's order (--order)".into());
            }
            let mut texts: Vec<(String, String)> = docs.values().filter(|d| g.holds(&d.uri))
                .map(|d| (d.uri.clone(), format!("{} {}", d.title.as_deref().unwrap_or(""), d.said.as_deref().unwrap_or("")))).collect();
            texts.sort();
            search::rank_texts(&texts, question).into_iter().map(|(id, _)| id).collect()
        }
    };
    let mut labeller = Describe { docs: &docs };
    // the lab's K6 on its own documents' text (kappa_state.relations: door-taken reads first, most recent first)
    let kappa: Option<Kappa> = if o.kappa {
        let docs = &docs;
        Some(Box::new(move |reads: &[lab::Read]| {
            let texts: Vec<String> = reads.iter().map(|r| docs.get(&r.doc).and_then(|d| d.said.clone()).unwrap_or_default()).collect();
            let via: Vec<Option<String>> = reads.iter().map(|r| r.via.clone()).collect();
            Ok(super::jev::relations(&texts, &via, 200, 6000, true, true))
        }))
    } else {
        None
    };
    let mut w = run(dir, &mut g, order, &mut labeller, question, o, kappa)?;
    for d in w.documents.iter_mut() {
        if let Some(x) = docs.get(&d.id) {
            d.label = x.title.clone().unwrap_or_else(|| d.id.clone());
            d.location = docs_path.map(|p| lab_pointer(p, &d.id));
        }
    }
    Ok(w)
}

/// The walk itself, on any graph and labeller: Jev ranks the doors when there is a key, search's order when not.
fn run(dir: &Path, g: &mut Graph, order: Vec<String>, labeller: &mut dyn DoorLabeller, question: &str, o: &Opts, kappa: Option<Kappa>) -> Result<AgentWalk> {
    let cfg = config(dir)?;
    let mut model = Model::open(dir, &cfg)?;
    let d = Settings::default();
    let (k, s8) = match o.reads {
        // operator a: no wave past the one that reaches `reads`, none when the seeds alone are enough
        Some(n) => {
            let seeds = o.seeds.unwrap_or(d.seeds);
            let waves = if n <= seeds { 0 } else { n.div_ceil(d.wave) as u32 };
            (n, Settings { waves, seeds, open: Some(1), max_reads: Some(n), ..d })
        }
        // k documents: s from search, then one door a wave until k are read; search only when no door is open
        None => {
            let k = o.budget;
            (k, Settings { waves: k as u32, seeds: o.seeds.unwrap_or(k.div_ceil(2)).min(k), wave: 1_000_000, per_wave: 0, open: Some(1), max_reads: Some(k), fill: false, within: "shown".into(), ..d })
        }
    };
    let seeds = s8.seeds;
    let (w, decider, note, costs) = if model.has_key() {
        let mut jev = JevDecider::new(&mut model);
        let with_kappa = kappa.is_some();
        jev.kappa = kappa;
        jev.keys = o.keys;
        let w = lab::run(g, order, s8, question, &mut jev, labeller)?;
        let name = if with_kappa { format!("{}, kappa K6", jev.name()) } else { jev.name() };
        (w, name, None, jev.waves)
    } else {
        let note = format!("no key, so the doors were ranked by search's order, not by Jev; set {} or run `midb key set`", cfg.model.key_env);
        let mut so = SearchOrder::new(&order);
        let w = lab::run(g, order, s8, question, &mut so, labeller)?;
        (w, "search-order".to_string(), Some(note), vec![])
    };
    // a read with no `via` is a target an earlier wave's door left pending: name that door
    let opened: Vec<&String> = w.batches.iter().flat_map(|b| b.opened.iter()).collect();
    let door_of = |r: &lab::Read| -> String {
        r.via.clone().unwrap_or_else(|| {
            opened.iter().rev().find(|k| w.clues.get(**k).is_some_and(|c| c.targets.contains(&r.doc))).map(|k| k.to_string()).unwrap_or_else(|| "search".into())
        })
    };
    let documents = w.reads.iter().take(k).enumerate().map(|(i, r)| Found {
        rank: i + 1,
        id: r.doc.clone(),
        label: r.doc.clone(),
        location: None,
        via: door_of(r),
        wave: r.wave,
    }).collect();
    let waves: Vec<WaveLog> = w.batches.iter().map(|b| WaveLog {
        wave: b.wave,
        doors: b.doors.len(),
        opened: b.opened.clone(),
        cost: costs.iter().find(|c| c.wave == b.wave).cloned(),
    }).collect();
    Ok(AgentWalk {
        question: question.into(),
        decider,
        note,
        budget: k,
        seeds,
        documents,
        requests: costs.iter().map(|c| c.requests).sum(),
        replayed: costs.iter().map(|c| c.replayed).sum(),
        called: costs.iter().map(|c| c.called).sum(),
        input_tokens: costs.iter().map(|c| c.input_tokens).sum(),
        cost_usd: costs.iter().map(|c| c.cost_usd).sum(),
        keys_read: w.keys_read,
        seconds: Default::default(),
        waves,
        trace: o.trace.then(|| Trace { batches: w.batches.clone(), doors: w.clues.values().cloned().collect(), reads: w.reads.clone() }),
    })
}

impl std::fmt::Display for AgentWalk {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        let doors = |n: usize| format!("{n} door{}", if n == 1 { "" } else { "s" });
        let reqs = |n: usize| format!("{n} request{}", if n == 1 { "" } else { "s" });
        writeln!(f, "walk: {} documents, {} from search then one door a wave; decider {}", self.documents.len(), self.seeds, self.decider)?;
        if let Some(n) = &self.note {
            writeln!(f, "note: {n}")?;
        }
        let iw = self.documents.iter().map(|d| d.id.len()).max().unwrap_or(0);
        let vw = self.documents.iter().map(|d| d.via.chars().count()).max().unwrap_or(0);
        for d in &self.documents {
            writeln!(f, "{:>4}  {:<iw$}  {:<vw$}  \"{}\"", d.rank, d.id, d.via, short(&d.label, 60))?;
            if let Some(l) = &d.location {
                writeln!(f, "      {l}")?;
            }
        }
        for w in &self.waves {
            let opened = if w.opened.is_empty() { "none".to_string() } else { w.opened.join(", ") };
            match &w.cost {
                Some(c) => writeln!(f, "wave {}: {} in {} ({} replayed, {} sent); opened {opened}", w.wave, doors(w.doors), reqs(c.requests), c.replayed, c.called)?,
                None => writeln!(f, "wave {}: {}; opened {opened}", w.wave, doors(w.doors))?,
            }
        }
        if self.requests > 0 {
            writeln!(f, "jev: {} ({} replayed, {} sent), {} input tokens, ${:.4}", reqs(self.requests), self.replayed, self.called, self.input_tokens, self.cost_usd)?;
        }
        Ok(())
    }
}

/// A document's content, from where it lives: the lab's docs.jsonl for `lab:`, else ingestion's reader.
pub fn content(dir: &Path, doc: &str, pointer: &str) -> Result<String> {
    if let Some(rest) = pointer.strip_prefix("lab:") {
        let (file, id) = rest.rsplit_once('#').ok_or_else(|| format!("{pointer}: a lab pointer is lab:<docs.jsonl>#<id>"))?;
        for line in std::fs::read_to_string(file).map_err(|e| format!("{file}: {e}"))?.lines() {
            let Ok(v) = serde_json::from_str::<serde_json::Value>(line) else { continue };
            if v["uri"].as_str() == Some(id) {
                return Ok(v["said"].as_str().unwrap_or_default().to_string());
            }
        }
        return Err(format!("{id} is not in {file}").into());
    }
    Reader::new(dir).text(doc, pointer)
}

/// Where a passage lives, for a person: a file passage's path (its pointer holds the source and byte range, its id
/// the path within the source), else the pointer itself.
fn location(doc: &str, pointer: &str) -> String {
    match (pointer.strip_prefix("doc:").and_then(|r| r.rsplit_once('#')), doc.rsplit_once('#')) {
        (Some((root, range)), Some((rel, _))) => {
            let path = Path::new(root).join(rel);
            format!("{} (bytes {range})", path.strip_prefix(".").unwrap_or(&path).display())
        }
        _ => pointer.to_string(),
    }
}

/// A document the walk returned, by id: its title, where it lives, then its content.
pub fn read_document(dir: &Path, corpus: &Corpus, id: &str) -> Result<String> {
    let (title, p) = match corpus {
        Corpus::Lab { docs: Some(d), .. } => {
            let p = lab_pointer(d, id);
            (id.to_string(), p)
        }
        Corpus::Lab { docs: None, .. } => return Err("this lab walk has no documents' text (--docs)".into()),
        Corpus::Project => {
            let (store, t) = open_project(dir)?;
            let mut g = Graph::open_items(&store, t).map_err(|_| NO_DOCUMENTS)?;
            if !g.holds(id) {
                return Err(format!("{id}: no such document; use an id a walk returned").into());
            }
            let title = g.values(id, Pred::Label)?.into_iter().next().unwrap_or_else(|| id.to_string());
            let p = g.values(id, Pred::Pointer)?.into_iter().next().ok_or_else(|| format!("{id}: it says nowhere where its content lives"))?;
            (title, p)
        }
    };
    Ok(format!("{id}  {title}\n{}\n\n{}", location(id, &p), content(dir, id, &p)?))
}
