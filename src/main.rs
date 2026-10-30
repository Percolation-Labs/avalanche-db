use std::collections::BTreeMap;
use std::io::Read;
use std::path::{Path, PathBuf};

use clap::{Parser, Subcommand};

use avalanche::config::{Config, DIR, FILE};
use avalanche::model::{date, Pred};
use avalanche::walk::session::{self, Steer};
use avalanche::store::{Dir, ScanCost, Store};
use avalanche::construct::{dream, ingest, review};
use avalanche::walk::{mcp, search, suite};
use avalanche::{infer, Result};

#[derive(Parser)]
#[command(name = "ava", version, about = "Avalanche DB: a memory you walk, not one you search")]
struct Cli {
    /// The folder holding avalanche.toml
    #[arg(long, short = 'C', default_value = ".", global = true)]
    dir: PathBuf,
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Write avalanche.toml from what is in this folder, and create the store
    Init,
    /// Read the configured sources into the store, as one transaction
    Ingest {
        /// Only these sources, by path or repo (all of them when none are named)
        sources: Vec<String>,
        /// Append a JSON-lines file of typed facts instead
        #[arg(long)]
        facts: Option<PathBuf>,
    },
    /// Set or check the decision model's key
    Key {
        #[command(subcommand)]
        action: KeyCmd,
    },
    /// Turn mentions into typed links with the decision model
    Dream {
        /// Say what it would ask and cost, and ask nothing
        #[arg(long)]
        dry_run: bool,
        /// Only sources dated on or after this day
        #[arg(long)]
        since: Option<String>,
    },
    /// The circle: records whose labels share words with the question
    Search { words: Vec<String> },
    /// Start a walk at the record these words best match
    Ask {
        words: Vec<String>,
        #[arg(long, default_value_t = 20)]
        budget: usize,
        /// Pin the walk to an earlier transaction
        #[arg(long)]
        as_of: Option<u64>,
        /// Walk only what was true on this date
        #[arg(long)]
        valid_at: Option<String>,
        /// Change the priority policy: kind=weight, comma separated (0 stops following a kind)
        #[arg(long, value_delimiter = ',')]
        prefer: Vec<String>,
    },
    /// Take one step of a walk: the best open question, or the one named by --take
    Step {
        token: String,
        #[arg(long)]
        take: Option<String>,
        #[arg(long, value_delimiter = ',')]
        prefer: Vec<String>,
    },
    /// Run a walk to its end and print what it reached
    Why {
        words: Vec<String>,
        #[arg(long, default_value_t = 20)]
        budget: usize,
        #[arg(long)]
        as_of: Option<u64>,
        #[arg(long)]
        valid_at: Option<String>,
        #[arg(long, value_delimiter = ',')]
        prefer: Vec<String>,
        /// Mark what changed against an earlier state: a transaction (T2) or a date
        #[arg(long)]
        changed_since: Option<String>,
    },
    /// Take a link back, with the reason; the rejection is kept as a fact
    Retract {
        s: String,
        pred: String,
        o: String,
        #[arg(long)]
        because: String,
    },
    /// Keep questions with what they reach, and walk them again to see what changed
    Suite {
        #[command(subcommand)]
        action: SuiteCmd,
    },
    /// Serve the session API to an agent over MCP, on stdin and stdout
    Mcp,
    /// A synthetic reachability world (REM-1195): import it, and walk its questions
    World {
        #[command(subcommand)]
        action: WorldCmd,
    },
    /// The walk lab's graphs (REM-1172 stage A): import them, and walk as the lab's engine over JSON lines
    Lab {
        #[command(subcommand)]
        action: LabCmd,
    },
    /// A node's links, as of a transaction and optionally valid on a date
    Edges {
        node: String,
        #[arg(long)]
        as_of: Option<u64>,
        #[arg(long)]
        valid_at: Option<String>,
        #[arg(long)]
        r#in: bool,
    },
    /// The store's transactions, or one transaction's facts
    Log { tx: Option<u64> },
    /// How the memory has been walked, read from the usage graph
    Usage,
}

#[derive(Subcommand)]
enum LabCmd {
    /// Read the lab's graphs.jsonl into a fresh store, one tenant per conversation
    Import {
        graphs: PathBuf,
        #[arg(long)]
        store: PathBuf,
        /// Only this conversation
        #[arg(long)]
        conv: Option<String>,
    },
    /// Walk on request over stdin and stdout, one JSON object a line: in {"walk": {conv, order, settings}}, out
    /// {"judge": {wave, clues, reads}} answered by {"p": {key: P}}, then {"done": walk}
    Serve {
        #[arg(long)]
        store: PathBuf,
    },
}

#[derive(Subcommand)]
enum WorldCmd {
    /// Read a reach.py world directory into a fresh store beside it (avalanche.redb)
    Import { world: PathBuf },
    /// Walk every question with the exploring walk and print one JSON line per question
    Walk {
        world: PathBuf,
        /// The reference's recorded P per clue (JSON lines: qid, kind, x, p)
        #[arg(long)]
        decisions: PathBuf,
        #[arg(long, default_value_t = 0.0)]
        eps: f64,
        #[arg(long, default_value_t = 1600)]
        max_reads: usize,
        /// Draw the near misses first: rejected clues with P at or above this
        #[arg(long)]
        band: Option<f64>,
        /// Clue kinds given P = 0
        #[arg(long, value_delimiter = ',')]
        blind: Vec<String>,
        /// Only this question
        #[arg(long)]
        qid: Option<String>,
    },
}

#[derive(Subcommand)]
enum SuiteCmd {
    /// Keep a question with what its walk reaches now
    Add {
        words: Vec<String>,
        #[arg(long, default_value_t = 20)]
        budget: usize,
        #[arg(long)]
        valid_at: Option<String>,
        #[arg(long, value_delimiter = ',')]
        prefer: Vec<String>,
    },
    /// Walk every kept question again; fails if any answer changed
    Run,
}

#[derive(Subcommand)]
enum KeyCmd {
    /// Read a key from stdin and keep it in ~/.config/avalanche/key
    Set,
    /// Ask the model one question with the key
    Check,
}

fn main() {
    if let Err(e) = run(Cli::parse()) {
        eprintln!("ava: {e}");
        std::process::exit(1);
    }
}

fn day(d: Option<String>) -> Result<Option<i64>> {
    d.map(|d| date::through(&d).ok_or_else(|| format!("{d}: not a date").into())).transpose()
}

fn open(dir: &Path) -> Result<(Config, Store, u32)> {
    let cfg = Config::load(dir)?;
    let store = Store::open(Config::store_path(dir))?;
    let t = store.tenant(&cfg.tenant)?;
    Ok((cfg, store, t))
}

fn run(cli: Cli) -> Result<()> {
    let dir = cli.dir.as_path();
    match cli.cmd {
        Cmd::Init => {
            if dir.join(FILE).exists() {
                return Err(format!("{FILE} already exists; edit it, or remove it to start again").into());
            }
            let cfg = Config::discover(dir)?;
            std::fs::write(dir.join(FILE), cfg.to_toml())?;
            std::fs::create_dir_all(dir.join(DIR))?;
            let store = Store::open(Config::store_path(dir))?;
            store.tenant(&cfg.tenant)?;
            println!("created {FILE} and {DIR}/store.redb (tenant \"{}\")", cfg.tenant);
            let srcs: Vec<String> = cfg.sources.iter().map(|s| format!("{} {}", s.adapter, s.path.display())).collect();
            println!("  sources: {}", if srcs.is_empty() { "none found".into() } else { srcs.join(", ") });
            let ids: Vec<String> = cfg.ids.iter().map(|(k, v)| format!("{k} {v}")).collect();
            println!("  ids: {}", if ids.is_empty() { "none found".into() } else { ids.join(", ") });
        }
        Cmd::Ingest { sources, facts } => {
            let started = std::time::Instant::now();
            let (cfg, store, t) = open(dir)?;
            let mut all = vec![];
            if let Some(f) = facts {
                all = ingest::json_lines(&f)?;
                println!("facts     {}  →  {} facts", f.display(), all.len());
            } else {
                let at_of = |src: &avalanche::config::SourceCfg| if src.adapter == "github" { src.repo.clone().unwrap_or_default() } else { src.path.display().to_string() };
                if let Some(missing) = sources.iter().find(|n| !cfg.sources.iter().any(|s| at_of(s) == **n)) {
                    return Err(format!("{missing}: not a source in {FILE}").into());
                }
                for src in cfg.sources.iter().filter(|s| sources.is_empty() || sources.contains(&at_of(s))) {
                    let at = at_of(src);
                    let got = match src.adapter.as_str() {
                        "git" => ingest::git_history(&dir.join(&src.path), src.rev.as_deref().unwrap_or("HEAD"), &at, &cfg)?,
                        "markdown" => match &src.rev {
                            Some(rev) => ingest::markdown_at(&dir.join(&src.path), rev, src.dir.as_deref().unwrap_or("."), &at, &cfg)?,
                            None => ingest::markdown(&dir.join(&src.path), &at, &cfg)?,
                        },
                        "percolate" => ingest::percolate(&dir.join(&src.path), &at, &cfg)?,
                        "github" => ingest::github(src.repo.as_deref().ok_or("a github source needs repo = \"owner/name\"")?, &cfg)?,
                        other => return Err(format!("{other}: no such adapter").into()),
                    };
                    println!("{:<9} {:<14} {} {:<8} →  {} facts", src.adapter, at, got.read.0, got.read.1, got.facts.len());
                    all.extend(got.facts);
                }
                let (n, facts) = review::facts(dir)?;
                if n > 0 {
                    println!("{:<9} {:<14} {} {:<8} →  {} facts", "reviews", format!("{DIR}/{}", review::FILE).trim_start_matches(".avalanche/"), n, if n == 1 { "review" } else { "reviews" }, facts.len());
                    all.extend(facts);
                }
            }
            let tx = store.write(t, &all)?;
            println!("T{tx}: {} facts in {:.1?}", all.len(), started.elapsed());
        }
        Cmd::Key { action: KeyCmd::Set } => {
            let mut k = String::new();
            std::io::stdin().read_to_string(&mut k)?;
            println!("kept in {}", infer::set_key(&k)?.display());
        }
        Cmd::Key { action: KeyCmd::Check } => {
            let cfg = Config::load(dir)?;
            println!("{}: key accepted", infer::check_key(&cfg)?);
        }
        Cmd::Dream { dry_run, since } => {
            let (cfg, store, t) = open(dir)?;
            let since = since.map(|d| date::parse(&d).ok_or(format!("{d}: not a date"))).transpose()?;
            let r = dream::dream(&store, t, dir, &cfg, &dream::Opts { dry_run, since })?;
            if r.dry_run {
                let srcs: Vec<String> = r.sources.iter().map(|(k, n)| format!("{n} {}{}", format!("{k:?}").to_lowercase(), if *n == 1 { "" } else { "s" })).collect();
                println!("{} mentions to decide, from {}", r.mentions, srcs.join(", "));
                println!("{} calls not yet recorded, about ${:.4} at {}; nothing asked", r.to_call, r.estimate, cfg.model.model);
                return Ok(());
            }
            let srcs: Vec<String> = r.sources.iter().map(|(k, n)| format!("{n} {}{}", format!("{k:?}").to_lowercase(), if *n == 1 { "" } else { "s" })).collect();
            println!("{} mentions to decide, from {}", r.mentions, srcs.join(", "));
            println!("asked {} questions in {} calls ({} replayed, {} called), ${:.4} billed", r.mentions, r.calls, r.replayed, r.calls - r.replayed, r.cost);
            let w = r.decisions.iter().map(|d| d.s.len()).max().unwrap_or(0);
            let ow = r.decisions.iter().map(|d| d.o.len()).max().unwrap_or(0);
            let mut only = vec![];
            let mut undecided = vec![];
            let already = r.decisions.iter().filter(|d| d.written).count();
            for d in r.decisions.iter().filter(|d| !d.written) {
                if d.choice == "only_mentions" {
                    only.push(format!("{} → {}", d.s, d.o));
                } else if r.rejected.contains(&format!("{} {} {}", d.s, d.choice, d.o)) {
                    continue;
                } else if d.p < dream::ACCEPT {
                    undecided.push(format!("{} {} {} ({:.2})", d.s, d.choice, d.o, d.p));
                } else {
                    println!("  {:<w$}  {:<10}  {:<ow$}  {:.2}", d.s, d.choice, d.o, d.p);
                }
            }
            println!("  only mentions: {}", if only.is_empty() { "none".into() } else { only.join(", ") });
            println!("  undecided (p < {}): {}", dream::ACCEPT, if undecided.is_empty() { "none".into() } else { undecided.join(", ") });
            if already > 0 {
                println!("  already linked: {already}");
            }
            if !r.rejected.is_empty() {
                println!("  rejected in review, not written: {}", r.rejected.join(", "));
            }
            match r.tx {
                Some(tx) => println!("T{tx}: {} facts", r.written),
                None => println!("nothing new to write"),
            }
        }
        Cmd::Search { words } => {
            let (_, store, t) = open(dir)?;
            let head = store.head(t)?;
            print!("{}", search::show(&search::search(&store, t, &words.join(" "), head, None)?));
        }
        Cmd::Ask { words, budget, as_of, valid_at, prefer } => {
            let (_, store, t) = open(dir)?;
            let s = session::ask(&store, t, &words.join(" "), budget, as_of, day(valid_at)?, &session::parse_prefer(&prefer)?)?;
            print!("{}", s.started());
        }
        Cmd::Step { token, take, prefer } => {
            let (_, store, t) = open(dir)?;
            print!("{}", session::step(&store, t, &token, &Steer { prefer: session::parse_prefer(&prefer)?, take })?);
        }
        Cmd::Why { words, budget, as_of, valid_at, prefer, changed_since } => {
            let (_, store, t) = open(dir)?;
            let (q, prefer) = (words.join(" "), session::parse_prefer(&prefer)?);
            let then = match changed_since {
                Some(c) => Some(match c.strip_prefix('T').and_then(|n| n.parse::<u64>().ok()) {
                    Some(tx) => session::walk(&store, t, &q, budget, Some(tx), None, &prefer)?,
                    None => session::walk(&store, t, &q, budget, as_of, day(Some(c))?, &prefer)?,
                }),
                None => None,
            };
            let s = session::walk(&store, t, &q, budget, as_of, day(valid_at)?, &prefer)?;
            print!("{}", session::why(&store, &s, then.as_ref())?);
        }
        Cmd::Retract { s, pred, o, because } => {
            let (_, store, t) = open(dir)?;
            let p = Pred::from_name(&pred).ok_or(format!("{pred}: not a link type"))?;
            let (tx, r) = review::retract(&store, t, dir, &s, p, &o, &because)?;
            println!("T{tx}: retracted {}, kept as {}", r.link(), r.review);
        }
        Cmd::Suite { action: SuiteCmd::Add { words, budget, valid_at, prefer } } => {
            let (_, store, t) = open(dir)?;
            let e = suite::add(&store, t, dir, &words.join(" "), budget, valid_at, prefer)?;
            let n = suite::read(dir)?.len();
            println!("kept: {} records reached; {n} question{} in {DIR}/{}", e.reached.len(), if n == 1 { "" } else { "s" }, suite::FILE);
        }
        Cmd::Suite { action: SuiteCmd::Run } => {
            let (_, store, t) = open(dir)?;
            let outcomes = suite::run(&store, t, dir)?;
            let changed = outcomes.iter().filter(|o| !o.gone.is_empty() || !o.new.is_empty()).count();
            for o in &outcomes {
                println!("{}  {}", if o.gone.is_empty() && o.new.is_empty() { "same   " } else { "changed" }, o.question);
                for g in &o.gone {
                    println!("  - {g}");
                }
                for n in &o.new {
                    println!("  + {n}");
                }
            }
            println!("{} of {} questions reach what they reached when kept", outcomes.len() - changed, outcomes.len());
            if changed > 0 {
                return Err(format!("{changed} of {} answers changed: review them, and keep a new answer with `ava suite add`", outcomes.len()).into());
            }
        }
        Cmd::Mcp => mcp::serve(dir)?,
        Cmd::World { action: WorldCmd::Import { world } } => {
            let path = world.join("avalanche.redb");
            let _ = std::fs::remove_file(&path);
            let store = Store::open(&path)?;
            let t = store.tenant("world")?;
            let started = std::time::Instant::now();
            let r = avalanche::construct::world::import(&store, t, &world)?;
            println!("T{}: {} items, {} facts in {:.1?}", r.tx, r.items, r.facts, started.elapsed());
        }
        Cmd::World { action: WorldCmd::Walk { world, decisions, eps, max_reads, band, blind, qid } } => {
            use avalanche::walk::{explore, world::World};
            let store = Store::open(world.join("avalanche.redb"))?;
            let t = store.tenant("world")?;
            let w = World::open(&store, t)?;
            let d = explore::Decisions::read(&std::fs::read_to_string(decisions)?)?;
            let o = explore::Opts { eps, max_reads, blind: &blind, band };
            for line in std::fs::read_to_string(world.join("questions.jsonl"))?.lines().filter(|l| !l.is_empty()) {
                let q: serde_json::Value = serde_json::from_str(line)?;
                let id = q["qid"].as_str().unwrap_or_default();
                if qid.as_deref().is_some_and(|x| x != id) {
                    continue;
                }
                let qv: Vec<f32> = q["vector"].as_array().ok_or("no vector")?.iter().map(|x| x.as_f64().unwrap_or(0.0) as f32).collect();
                let started = std::time::Instant::now();
                w.cost.set(0);
                let r = explore::explore(&w, id, &qv, &d, &o)?;
                let order: Vec<String> = r.order.iter().map(|x| w.name(*x)).collect::<Result<_>>()?;
                println!("{}", serde_json::json!({"qid": id, "order": order, "why": r.why, "front": r.front, "front_small": r.front_small,
                    "keys_read": w.cost.get(), "micros": started.elapsed().as_micros() as u64}));
            }
        }
        Cmd::Lab { action: LabCmd::Import { graphs, store, conv } } => {
            if store.exists() && conv.is_none() {
                return Err(format!("{} exists; the lab imports into a fresh store", store.display()).into());
            }
            let s = Store::open(&store)?;
            let started = std::time::Instant::now();
            let r = avalanche::construct::lab::import(&s, &graphs, conv.as_deref())?;
            let (docs, facts): (usize, usize) = r.iter().fold((0, 0), |a, x| (a.0 + x.docs, a.1 + x.facts));
            println!("{} conversations, {docs} documents, {facts} facts in {:.1?}", r.len(), started.elapsed());
        }
        Cmd::Lab { action: LabCmd::Serve { store } } => lab_serve(&store)?,
        Cmd::Edges { node, as_of, valid_at, r#in } => {
            let (_, store, t) = open(dir)?;
            let head = store.head(t)?;
            let as_of = as_of.unwrap_or(head);
            let id = store.id(t, &node)?.ok_or(format!("{node} is not in the store"))?;
            let edges = store.edges(t, id, if r#in { Dir::In } else { Dir::Out }, as_of, day(valid_at)?, &mut ScanCost::default())?;
            for e in &edges {
                let arrow = if r#in { format!("<-{}-", e.pred.name()) } else { format!("-{}->", e.pred.name()) };
                println!("  {arrow} {}  [{}; T{}; valid from {}]", store.name(t, e.other)?, store.name(t, e.graph)?.trim_start_matches("graph:"), e.tx, date::show(e.valid_from));
            }
            println!("{} links at T{as_of} of T{head}", edges.len());
        }
        Cmd::Log { tx: None } => {
            let (_, store, t) = open(dir)?;
            for (tx, wall, n) in store.transactions(t)? {
                println!("T{tx}  {}  {n} facts", date::show(wall));
            }
        }
        Cmd::Log { tx: Some(tx) } => {
            let (_, store, t) = open(dir)?;
            for (s, p, o, g, retract) in store.log(t, tx)? {
                println!("{}{s} {} {o}  [{}]", if retract { "RETRACT " } else { "" }, p.name(), g.trim_start_matches("graph:"));
            }
        }
        Cmd::Usage => {
            let (_, store, data) = open(dir)?;
            let t = store.usage_of(data)?;
            let head = store.head(t)?;
            let mut cost = ScanCost::default();
            let usage = store.graph_id(t, "usage")?;
            let sessions = store.by_pred(t, Pred::Asked, head, &mut cost)?.len();
            let steps = store.by_pred(t, Pred::InSession, head, &mut cost)?.len();
            let mut per_node: BTreeMap<String, usize> = BTreeMap::new();
            for (_, o, g) in store.by_pred(t, Pred::Visited, head, &mut cost)? {
                if Some(g) == usage {
                    *per_node.entry(store.name(t, o)?).or_default() += 1;
                }
            }
            let mut kinds: BTreeMap<String, usize> = BTreeMap::new();
            for (_, o, _) in store.by_pred(t, Pred::Via, head, &mut cost)? {
                let k = store.name(t, o)?.trim_start_matches("lit:").to_string();
                if k != "start" {
                    *kinds.entry(k).or_default() += 1;
                }
            }
            let mut top: Vec<_> = per_node.into_iter().collect();
            top.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
            let mut kinds: Vec<_> = kinds.into_iter().collect();
            kinds.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
            println!("{sessions} sessions, {steps} steps");
            println!("most walked: {}", top.iter().take(3).map(|(n, c)| format!("{n} ({c})")).collect::<Vec<_>>().join(", "));
            println!("link kinds walked: {}", kinds.iter().map(|(k, c)| format!("{k} {c}")).collect::<Vec<_>>().join(", "));
        }
    }
    Ok(())
}

/// `ava lab serve`: the lab's engine over JSON lines, so walklab's deciders, scorecard and fidelity check drive it.
fn lab_serve(path: &Path) -> Result<()> {
    use std::io::{BufRead, Write};
    use avalanche::walk::lab;
    let store = Store::open(path)?;
    let stdin = std::io::stdin();
    let mut lines = stdin.lock().lines();
    let mut out = std::io::stdout().lock();
    while let Some(line) = lines.next() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        let req: serde_json::Value = serde_json::from_str(&line)?;
        let w = &req["walk"];
        let res = (|| -> Result<lab::Walk> {
            let conv = w["conv"].as_str().ok_or("a walk request names its conv")?;
            let order: Vec<String> = serde_json::from_value(w["order"].clone())?;
            let settings: lab::Settings = serde_json::from_value(w.get("settings").cloned().unwrap_or(serde_json::json!({})))?;
            let mut g = lab::Graph::open(&store, conv)?;
            let mut decide = |wave: u32, clues: &BTreeMap<String, lab::Clue>, walk: &lab::Walk| -> Result<std::collections::HashMap<String, f64>> {
                let msg = serde_json::json!({"judge": {"wave": wave, "clues": clues.values().collect::<Vec<_>>(), "reads": walk.reads}});
                writeln!(out, "{msg}")?;
                out.flush()?;
                let ans = lines.next().ok_or("stdin closed while a judgement was asked")??;
                let v: serde_json::Value = serde_json::from_str(&ans)?;
                let mut got = std::collections::HashMap::new();
                for (k, p) in v["p"].as_object().ok_or("an answer is {\"p\": {key: P}}")? {
                    if let Some(p) = p.as_f64() {
                        got.insert(k.clone(), p);
                    }
                }
                Ok(got)
            };
            lab::run(&mut g, order, settings, &mut decide)
        })();
        let msg = match res {
            Ok(walk) => serde_json::json!({"done": walk}),
            Err(e) => serde_json::json!({"error": e.to_string()}),
        };
        writeln!(out, "{msg}")?;
        out.flush()?;
    }
    Ok(())
}
