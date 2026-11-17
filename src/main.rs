use std::collections::BTreeMap;
use std::io::Read;
use std::path::{Path, PathBuf};

use clap::{Parser, Subcommand};

use avalanche::config::{Config, DIR};
use avalanche::model::{date, Pred};
use avalanche::walk::session::{self, Steer};
use avalanche::store::{Dir, ScanCost, Store};
use avalanche::construct::{dream, project, review};
use avalanche::walk::{agent, mcp, p8ql, search, suite};
use avalanche::{infer, Result};

#[derive(Parser)]
#[command(name = "midb", version, about = "Avalanche DB: a memory you walk, not one you search")]
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
        /// Bring your own files: add this folder, repository or .jsonl as a `documents` source (creating the
        /// config and store when there are none) and ingest it
        #[arg(long)]
        documents: Option<String>,
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
    Search {
        words: Vec<String>,
        /// Search the ingested documents' full text (BM25) instead of labels
        #[arg(long)]
        text: bool,
    },
    /// The doors one ingested passage opens, as the D6 door shows them to a decider
    Doors {
        /// A passage id, as `midb search --text` prints it (`README.md#2`, `commit/1a2b3c4d5e`)
        doc: String,
        /// Terms held by more passages than this raise no door (the walk's cap)
        #[arg(long, default_value_t = 100)]
        cap: usize,
    },
    /// Run a P8QL statement (specs/p8ql.md): each clause is one walk step
    Query {
        statement: Vec<String>,
        /// Print the plan without running it
        #[arg(long)]
        explain: bool,
    },
    /// What a P8QL statement can name: kinds, link types and named paths
    Schema,
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
    /// Serve the session API and the agent walk over MCP, on stdin and stdout; `mcp install` registers it with Claude
    Mcp {
        #[command(subcommand)]
        action: Option<McpCmd>,
        #[command(flatten)]
        corpus: CorpusArgs,
    },
    /// The walk an agent calls: the documents a question needs, with where each lives and how the walk reached it
    Walk {
        question: Vec<String>,
        /// How many documents to return (k)
        #[arg(long, default_value_t = 10)]
        budget: usize,
        /// How many of them full-text search picks before the walk follows doors (s; default ceil(k/2), or 10 with --reads)
        #[arg(long)]
        seeds: Option<usize>,
        /// Expert: the lab's operator a instead (waves of 50 filled by search, one door a wave), stopping at this many
        /// documents; --budget is then ignored
        #[arg(long)]
        reads: Option<usize>,
        /// Print JSON
        #[arg(long)]
        json: bool,
        /// Leave the walk's past (kappa, K6) out of Jev's requests: the control
        #[arg(long)]
        no_kappa: bool,
        /// How Jev's options are named: f2 (as measured) or c (c0, c1, ..., the lab's jevcache, for parity)
        #[arg(long, default_value = "f2")]
        keys: avalanche::walk::jev::Keys,
        /// Search's order from a file (a JSON list of document ids) instead of the store's own search
        #[arg(long)]
        order: Option<PathBuf>,
        #[command(flatten)]
        corpus: CorpusArgs,
    },
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

/// Where a walk's documents are: this folder's store, or a lab-imported conversation.
#[derive(clap::Args)]
struct CorpusArgs {
    /// A lab-imported store (`midb lab import`) instead of this folder's
    #[arg(long)]
    store: Option<PathBuf>,
    /// The conversation in that store
    #[arg(long, requires = "store")]
    conv: Option<String>,
    /// The documents' text, a docs.jsonl (uri, title, said, ...), for door text, search and read_document
    #[arg(long, requires = "store")]
    docs: Option<PathBuf>,
}

impl CorpusArgs {
    fn corpus(self) -> Result<agent::Corpus> {
        Ok(match self.store {
            None => agent::Corpus::Project,
            Some(store) => agent::Corpus::Lab { store, conv: self.conv.ok_or("--store needs --conv")?, docs: self.docs },
        })
    }
}

#[derive(Subcommand)]
enum McpCmd {
    /// Register this store with Claude Code (`claude mcp add`), or print the command and config when claude is not here
    Install {
        /// Claude Code's scope: local, user or project
        #[arg(long, default_value = "user")]
        scope: String,
    },
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
    /// Walk on request over stdin and stdout, one JSON object a line: in {"walk": {conv, order, settings, question}},
    /// out {"judge": {wave, clues, attrs, label_version, reads}} answered by {"p": {key: P}} or {"keep", "rank"},
    /// then {"done": walk}. Specs: specs/doors.md
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
        eprintln!("midb: {e}");
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
        Cmd::Init => print!("{}", project::init(dir)?),
        Cmd::Ingest { sources, facts, documents } => match documents {
            Some(p) => print!("{}", project::ingest_documents(dir, &p)?),
            None => print!("{}", project::ingest(dir, &sources, facts)?),
        },
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
        Cmd::Doors { doc, cap } => {
            let (_, store, t) = open(dir)?;
            let mut g = avalanche::walk::lab::Graph::open_items(&store, t)?;
            let mut d6 = avalanche::walk::d6::D6::new(dir);
            for door in avalanche::walk::d6::doors_of(&mut g, &doc, cap)? {
                println!("{}\n  {}\n", door.key, d6.lines(&door, &mut g)?.join("\n  "));
            }
        }
        Cmd::Search { words, text: true } => {
            let (_, store, t) = open(dir)?;
            let mut g = avalanche::walk::lab::Graph::open_items(&store, t)?;
            let ft = avalanche::walk::text::FullText::open(dir, t, store.head(t)?, &mut g)?;
            let hits = ft.search(&words.join(" "));
            for (d, s) in hits.iter().take(10) {
                let title = g.values(d, Pred::Label)?.into_iter().next().unwrap_or_default();
                println!("  {d:<40}  {:<60}  {s:.2}", avalanche::model::short(&title, 60));
            }
            println!("{} passages share a word with the question; the best {} shown", hits.len(), hits.len().min(10));
        }
        Cmd::Search { words, .. } => {
            let (_, store, t) = open(dir)?;
            let head = store.head(t)?;
            print!("{}", search::show(&search::search(&store, t, &words.join(" "), head, None)?));
        }
        Cmd::Query { statement, explain } => {
            let (cfg, store, t) = open(dir)?;
            let stmt = p8ql::parse(&statement.join(" "), &cfg.paths)?;
            if explain {
                print!("{}", p8ql::explain(&store, t, &stmt)?);
            } else {
                match p8ql::run(&store, t, &stmt)? {
                    p8ql::Outcome::Done(s) | p8ql::Outcome::Paused(s) => print!("{s}"),
                }
            }
        }
        Cmd::Schema => {
            let (cfg, store, t) = open(dir)?;
            print!("{}", p8ql::schema(&store, t, &cfg.paths)?);
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
                return Err(format!("{changed} of {} answers changed: review them, and keep a new answer with `midb suite add`", outcomes.len()).into());
            }
        }
        Cmd::Mcp { action: Some(McpCmd::Install { scope }), corpus } => print!("{}", mcp::install(dir, &corpus.corpus()?, &scope)?),
        Cmd::Mcp { action: None, corpus } => mcp::serve(dir, &corpus.corpus()?)?,
        Cmd::Walk { question, budget, seeds, reads, json, no_kappa, keys, order, corpus } => {
            let order = order.map(|p| -> Result<Vec<String>> { Ok(serde_json::from_str(&std::fs::read_to_string(&p).map_err(|e| format!("{}: {e}", p.display()))?)?) }).transpose()?;
            let w = agent::walk(dir, &corpus.corpus()?, &question.join(" "), &agent::Opts { budget, seeds, reads, order, kappa: !no_kappa, keys })?;
            if json {
                println!("{}", serde_json::to_string_pretty(&w)?);
            } else {
                print!("{w}");
            }
        }
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

/// `midb lab serve`: the lab's engine over JSON lines, so an outside decider drives it (specs/doors.md).
///
/// In: {"walk": {conv, order, settings, question?}}. Each wave the engine writes {"judge": {wave, clues, attrs,
/// label_version, reads}} and reads one answer: {"p": {key: P}} (scores; with `gate` in the settings, the V0 gate) or
/// {"keep": [keys], "rank": [keys]} (filter, then rank). Under `within: decider` the engine also writes
/// {"targets": {wave, door, targets}} for each door it opens, answered by {"order": [docs]}. Then {"done": walk}.
fn lab_serve(path: &Path) -> Result<()> {
    use std::io::{BufRead, Write};
    use avalanche::walk::{doors, lab};
    let store = Store::open(path)?;
    let stdin = std::io::stdin();
    let mut lines = stdin.lock().lines();
    let mut out = std::io::stdout().lock();

    /// The outside decider: one round trip per wave, cached so the filter and rank passes ask once.
    struct Remote<'a, I: Iterator<Item = std::io::Result<String>>, W: Write> {
        lines: &'a mut I,
        out: &'a mut W,
        wave: Option<u32>,
        keep: Option<std::collections::BTreeSet<String>>,
        rank: Vec<doors::Ranked>,
    }
    impl<I: Iterator<Item = std::io::Result<String>>, W: Write> Remote<'_, I, W> {
        fn ask(&mut self, b: &doors::Batch) -> Result<()> {
            if self.wave == Some(b.wave) {
                return Ok(());
            }
            let msg = serde_json::json!({"judge": {"wave": b.wave, "clues": b.doors.values().collect::<Vec<_>>(), "attrs": b.attrs, "label_version": b.label_version, "reads": b.reads}});
            writeln!(self.out, "{msg}")?;
            self.out.flush()?;
            let ans = self.lines.next().ok_or("stdin closed while a judgement was asked")??;
            let v: serde_json::Value = serde_json::from_str(&ans)?;
            self.keep = match v.get("keep") {
                Some(k) => Some(serde_json::from_value(k.clone())?),
                None => None,
            };
            self.rank = if let Some(r) = v.get("rank") {
                let keys: Vec<String> = serde_json::from_value(r.clone())?;
                keys.into_iter().map(|key| doors::Ranked { key, score: None }).collect()
            } else {
                let p = v["p"].as_object().ok_or("an answer is {\"p\": {key: P}} or {\"keep\": [...], \"rank\": [...]}")?;
                let mut r: Vec<(String, f64)> = p.iter().filter_map(|(k, p)| p.as_f64().map(|p| (k.clone(), p))).collect();
                r.sort_by(|a, b| b.1.total_cmp(&a.1).then_with(|| lab::collate(&a.0).cmp(&lab::collate(&b.0))));
                r.into_iter().map(|(key, s)| doors::Ranked { key, score: Some(s) }).collect()
            };
            self.wave = Some(b.wave);
            Ok(())
        }
    }
    impl<I: Iterator<Item = std::io::Result<String>>, W: Write> doors::Decider for Remote<'_, I, W> {
        fn name(&self) -> String {
            "remote".into()
        }
        fn filter(&mut self, b: &doors::Batch) -> Result<Option<std::collections::BTreeSet<String>>> {
            self.ask(b)?;
            Ok(self.keep.clone())
        }
        fn rank(&mut self, b: &doors::Batch) -> Result<Vec<doors::Ranked>> {
            self.ask(b)?;
            Ok(self.rank.clone())
        }
        /// Under `within: decider`: {"targets": {wave, door, targets}} answered by {"order": [docs]} or {"order": null}.
        fn rank_targets(&mut self, _q: &str, door: &lab::Clue, targets: &[String]) -> Result<Option<Vec<String>>> {
            let msg = serde_json::json!({"targets": {"wave": self.wave, "door": door.key, "targets": targets}});
            writeln!(self.out, "{msg}")?;
            self.out.flush()?;
            let ans = self.lines.next().ok_or("stdin closed while a target order was asked")??;
            let v: serde_json::Value = serde_json::from_str(&ans)?;
            Ok(serde_json::from_value(v.get("order").cloned().unwrap_or(serde_json::Value::Null))?)
        }
    }

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
            let question = w["question"].as_str().unwrap_or_default().to_string();
            let mut g = lab::Graph::open(&store, conv)?;
            let mut remote = Remote { lines: &mut lines, out: &mut out, wave: None, keep: None, rank: vec![] };
            lab::run(&mut g, order, settings, &question, &mut remote, &mut doors::GraphStats)
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
