use std::collections::BTreeMap;
use std::path::PathBuf;
use std::time::Instant;

use clap::{Parser, Subcommand};

use avalanche::ingest;
use avalanche::model::{date, FactIn, Pred};
use avalanche::session::{self, DEFAULT_FOLLOW, USAGE};
use avalanche::store::{Dir, ScanCost, Store};
use avalanche::Result;

#[derive(Parser)]
#[command(name = "ava", about = "Avalanche DB: a local bitemporal graph on redb")]
struct Cli {
    #[arg(long, default_value = "avalanche.redb", global = true)]
    db: PathBuf,
    #[arg(long, default_value = "sirsh", global = true)]
    tenant: String,
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Append a source to the log as one transaction
    Ingest {
        #[command(subcommand)]
        source: Source,
    },
    /// Start a session at the question these words name
    Ask {
        words: Vec<String>,
        #[arg(long, default_value_t = 40)]
        budget: usize,
        /// Pin the session to an earlier transaction
        #[arg(long)]
        as_of: Option<u64>,
    },
    /// Take one step of a session
    Step {
        token: String,
        /// Predicates to follow, most wanted first (default: answers,makes,informs,mentions,cites,authoredBy,touches)
        #[arg(long, value_delimiter = ',')]
        follow: Vec<String>,
    },
    /// A node's edges, as of a transaction and optionally valid at a date
    Edges {
        node: String,
        #[arg(long)]
        as_of: Option<u64>,
        #[arg(long)]
        valid_at: Option<String>,
        #[arg(long)]
        r#in: bool,
    },
    /// The tenant's transactions, or one transaction's facts
    Log { tx: Option<u64> },
    /// Metrics read from the usage graph
    Usage,
}

#[derive(Subcommand)]
enum Source {
    Git {
        repo: PathBuf,
        #[arg(long, default_value = "HEAD")]
        rev: String,
        #[arg(long)]
        max: Option<usize>,
    },
    Cards {
        repo: PathBuf,
        #[arg(long, default_value = "HEAD")]
        rev: String,
    },
    Facts { file: PathBuf },
}

fn main() {
    if let Err(e) = run(Cli::parse()) {
        eprintln!("ava: {e}");
        std::process::exit(1);
    }
}

fn run(cli: Cli) -> Result<()> {
    let store = Store::open(&cli.db)?;
    let t = store.tenant(&cli.tenant)?;
    match cli.cmd {
        Cmd::Ingest { source } => {
            let started = Instant::now();
            let facts: Vec<FactIn> = match source {
                Source::Git { repo, rev, max } => ingest::git_history(&repo, &rev, max)?,
                Source::Cards { repo, rev } => ingest::board_cards(&repo, &rev)?,
                Source::Facts { file } => ingest::json_lines(&file)?,
            };
            let read = started.elapsed();
            let tx = store.write(t, &facts)?;
            println!("T{tx}: {} facts ({} retractions); read {:.1?}, written {:.1?}", facts.len(), facts.iter().filter(|f| f.retract).count(), read, started.elapsed() - read);
        }
        Cmd::Ask { words, budget, as_of } => {
            let s = session::ask(&store, t, &words.join(" "), budget, as_of)?;
            println!("session {} at {} pinned to T{} (budget {})\n  token: {}", s.id, s.question, s.snapshot, s.budget, s.token());
        }
        Cmd::Step { token, follow } => {
            let follow: Vec<Pred> = if follow.is_empty() {
                DEFAULT_FOLLOW.to_vec()
            } else {
                follow.iter().map(|p| Pred::from_name(p).ok_or_else(|| format!("{p}: not a predicate"))).collect::<std::result::Result<_, _>>()?
            };
            print!("{}", session::step(&store, &token, &follow)?);
        }
        Cmd::Edges { node, as_of, valid_at, r#in } => {
            let head = store.head(t)?;
            let as_of = as_of.unwrap_or(head);
            let valid = valid_at.as_deref().map(|d| date::parse(d).ok_or(format!("{d}: not a date"))).transpose()?;
            let id = store.id(t, &node)?.ok_or(format!("{node} is not in the store"))?;
            let mut cost = ScanCost::default();
            let started = Instant::now();
            let edges = store.edges(t, id, if r#in { Dir::In } else { Dir::Out }, as_of, valid, &mut cost)?;
            for e in &edges {
                let arrow = if r#in { format!("<-{}-", e.pred.name()) } else { format!("-{}->", e.pred.name()) };
                println!("  {arrow} {}  [{}; T{}; valid {} .. {}]", store.name(t, e.other)?, store.name(t, e.graph)?.trim_start_matches("graph:"), e.tx, date::show(e.valid_from), date::show(e.valid_to));
            }
            println!("{} edges at T{as_of} of T{head}; {} keys in {:.1?}", edges.len(), cost.keys_read, started.elapsed());
        }
        Cmd::Log { tx: None } => {
            for (tx, wall, n) in store.transactions(t)? {
                println!("T{tx}  {}  {n} facts", date::show(wall));
            }
        }
        Cmd::Log { tx: Some(tx) } => {
            for (s, p, o, g, retract) in store.log(t, tx)? {
                println!("{}{s} {} {o}  [{}]", if retract { "RETRACT " } else { "" }, p.name(), g.trim_start_matches("graph:"));
            }
        }
        Cmd::Usage => {
            let head = store.head(t)?;
            let mut cost = ScanCost::default();
            let usage = store.graph_id(t, USAGE)?;
            let sessions = store.by_pred(t, Pred::Asked, head, &mut cost)?.len();
            let steps = store.by_pred(t, Pred::InSession, head, &mut cost)?;
            let mut per_node: BTreeMap<u64, usize> = BTreeMap::new();
            for (_, o, g) in store.by_pred(t, Pred::Visited, head, &mut cost)? {
                if Some(g) == usage {
                    *per_node.entry(o).or_default() += 1;
                }
            }
            let mut top: Vec<_> = per_node.into_iter().collect();
            top.sort_by(|a, b| b.1.cmp(&a.1));
            println!("{sessions} sessions, {} steps, {} distinct nodes visited; usage graph holds {} facts", steps.len(), top.len(), usage.map(|g| store.graph_size(t, g, head)).transpose()?.unwrap_or(0));
            println!("most walked:");
            for (node, n) in top.iter().take(10) {
                println!("  {n:>3}  {}", store.name(t, *node)?);
            }
            println!("({} keys read)", cost.keys_read);
        }
    }
    Ok(())
}
