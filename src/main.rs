use std::collections::BTreeMap;
use std::io::Read;
use std::path::{Path, PathBuf};

use clap::{Parser, Subcommand};

use avalanche::config::{Config, DIR, FILE};
use avalanche::model::{date, Pred};
use avalanche::walk::session::{self, Steer};
use avalanche::store::{Dir, ScanCost, Store};
use avalanche::construct::{dream, ingest};
use avalanche::walk::search;
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
    /// Read every configured source into the store, as one transaction
    Ingest {
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
    Dream,
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
        valid_at: Option<String>,
        #[arg(long, value_delimiter = ',')]
        prefer: Vec<String>,
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
    // A date means the whole day: valid at its last second.
    d.map(|d| date::parse(&d).map(|t| if d.len() == 10 { t + 86399 } else { t }).ok_or_else(|| format!("{d}: not a date").into())).transpose()
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
        Cmd::Ingest { facts } => {
            let (cfg, store, t) = open(dir)?;
            let mut all = vec![];
            if let Some(f) = facts {
                all = ingest::json_lines(&f)?;
                println!("facts     {}  →  {} facts", f.display(), all.len());
            } else {
                for src in &cfg.sources {
                    let at = src.path.display().to_string();
                    let got = match src.adapter.as_str() {
                        "git" => ingest::git_history(&dir.join(&src.path), &at, &cfg)?,
                        "markdown" => ingest::markdown(&dir.join(&src.path), &at, &cfg)?,
                        other => return Err(format!("{other}: no such adapter").into()),
                    };
                    println!("{:<9} {:<8} {} {:<8} →  {} facts", src.adapter, at, got.read.0, got.read.1, got.facts.len());
                    all.extend(got.facts);
                }
            }
            let tx = store.write(t, &all)?;
            println!("T{tx}: {} facts", all.len());
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
        Cmd::Dream => {
            let (cfg, store, t) = open(dir)?;
            let r = dream::dream(&store, t, dir, &cfg)?;
            let srcs: Vec<String> = r.sources.iter().map(|(k, n)| format!("{n} {}{}", format!("{k:?}").to_lowercase(), if *n == 1 { "" } else { "s" })).collect();
            println!("{} mentions to decide, from {}", r.mentions, srcs.join(", "));
            println!("asked {} questions in {} calls ({} replayed, {} called), ${:.4}", r.mentions, r.calls, r.replayed, r.calls - r.replayed, r.cost);
            let w = r.decisions.iter().map(|d| d.s.len()).max().unwrap_or(0);
            let ow = r.decisions.iter().map(|d| d.o.len()).max().unwrap_or(0);
            let mut only = vec![];
            let mut undecided = vec![];
            for d in &r.decisions {
                if d.choice == "only_mentions" {
                    only.push(format!("{} → {}", d.s, d.o));
                } else if d.p < dream::ACCEPT {
                    undecided.push(format!("{} {} {} ({:.2})", d.s, d.choice, d.o, d.p));
                } else {
                    println!("  {:<w$}  {:<10}  {:<ow$}  {:.2}", d.s, d.choice, d.o, d.p);
                }
            }
            println!("  only mentions: {}", if only.is_empty() { "none".into() } else { only.join(", ") });
            println!("  undecided (p < {}): {}", dream::ACCEPT, if undecided.is_empty() { "none".into() } else { undecided.join(", ") });
            match r.tx {
                Some(tx) => println!("T{tx}: {} facts", r.written),
                None => println!("nothing new to write"),
            }
        }
        Cmd::Search { words } => {
            let (_, store, t) = open(dir)?;
            let head = store.head(t)?;
            let hits = search::search(&store, t, &words.join(" "), head, None)?;
            let w = hits.iter().map(|h| h.node.len()).max().unwrap_or(0);
            let lw = hits.iter().map(|h| h.label.len()).max().unwrap_or(0) + 2;
            for h in hits.iter().take(5) {
                println!("  {:<w$}  {:<lw$}  {:.2}", h.node, format!("\"{}\"", h.label), h.score);
            }
            println!("{} records share a word with the question{}", hits.len(), if hits.len() > 5 { "; the best 5 shown" } else { "" });
        }
        Cmd::Ask { words, budget, as_of, valid_at, prefer } => {
            let (_, store, t) = open(dir)?;
            let s = session::ask(&store, t, &words.join(" "), budget, as_of, day(valid_at)?, &session::parse_prefer(&prefer)?)?;
            println!("session {} at {}, pinned to T{}, budget {}\n  token {}", s.id, s.start, s.snapshot, s.budget, s.token());
        }
        Cmd::Step { token, take, prefer } => {
            let (_, store, t) = open(dir)?;
            print!("{}", session::step(&store, t, &token, &Steer { prefer: session::parse_prefer(&prefer)?, take })?);
        }
        Cmd::Why { words, budget, valid_at, prefer } => {
            let (_, store, t) = open(dir)?;
            let s = session::walk(&store, t, &words.join(" "), budget, day(valid_at)?, &session::parse_prefer(&prefer)?)?;
            print!("{}", session::why(&store, &s)?);
        }
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
