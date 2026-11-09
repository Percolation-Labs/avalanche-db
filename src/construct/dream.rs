//! CONSTRUCT, by inference: dreaming turns plain mentions into typed links. Code finds the
//! candidates (every id a note or commit names) and reads the evidence; the model judges
//! only what one mention means, as one Choice over the link types that fit those two kinds,
//! plus `only_mentions`. Links are written only at p >= ACCEPT.

use std::collections::BTreeMap;
use std::path::Path;

use crate::config::Config;
use crate::infer::{Choice, Model, Outcome};
use crate::model::{FactIn, Kind, Pred};
use crate::store::{Dir, ScanCost, Store};
use crate::Result;

/// Answers below this probability are kept in the recording but written as no link.
pub const ACCEPT: f64 = 0.8;
pub const ONLY: &str = "only_mentions";

/// The link types a mention from `s` to `o` may turn into, with what each means.
fn options(s: Kind, o: Kind, target: &str) -> Vec<(String, String)> {
    let v: Vec<(&str, String)> = match (s, o) {
        (Kind::Decision, Kind::Issue) => vec![("because", format!("`record` is a decision made because of {target}"))],
        (Kind::Decision, Kind::Proposal) => vec![
            ("rejects", format!("`record` decides against {target}")),
            ("adopts", format!("`record` decides to adopt {target}")),
        ],
        (Kind::Card, Kind::Card) => vec![("because", format!("`record` gives {target} as a reason for what it decides or asks"))],
        (Kind::Decision, Kind::File) => vec![("decides", format!("`record` decides how {target} must work"))],
        (Kind::Issue, Kind::Issue) => vec![("duplicates", format!("`record` reports the same problem as {target}"))],
        (Kind::Commit | Kind::Pr, Kind::Issue) => vec![("fixes", format!("`record` is a change that fixes {target}"))],
        (Kind::Commit | Kind::Pr, Kind::Decision | Kind::Card) => vec![("implements", format!("`record` is a change that carries out {target}"))],
        (Kind::Claim, Kind::Decision | Kind::Card | Kind::Proposal) => vec![
            ("supports", format!("`record` is a reading that argues for {target}")),
            ("challenges", format!("`record` is a reading that argues against {target}, or names a cost of it")),
        ],
        _ => vec![],
    };
    if v.is_empty() {
        return vec![];
    }
    let mut v: Vec<(String, String)> = v.into_iter().map(|(k, d)| (k.to_string(), d)).collect();
    // Cards name other cards to rule them out of scope, as related or later work, or as what
    // they wait on; the stand-in read those as reasons (REM-1331 round 5: 4 of 11, all at 0.80).
    let only = if (s, o) == (Kind::Card, Kind::Card) {
        format!("`record` names {target} but not as a reason: to put it out of scope, as related or later work, or as something it depends on or waits for")
    } else {
        format!("`record` names {target} but none of the above holds")
    };
    v.push((ONLY.into(), only));
    v
}

/// The link types dreaming writes.
const WRITES: &[Pred] = &[Pred::Because, Pred::Rejects, Pred::Adopts, Pred::Decides, Pred::Duplicates, Pred::Fixes, Pred::Implements, Pred::Supports, Pred::Challenges];

pub struct Decision {
    pub s: String,
    pub o: String,
    pub choice: String,
    pub p: f64,
    /// The link is already in the store, from an earlier dream.
    pub written: bool,
}

#[derive(Default)]
pub struct Opts {
    /// Say what it would ask and what it would cost, and ask nothing.
    pub dry_run: bool,
    /// Only sources that became true on or after this time.
    pub since: Option<i64>,
}

pub struct Report {
    pub dry_run: bool,
    /// Calls not yet recorded, and what they would cost.
    pub to_call: usize,
    pub estimate: f64,
    pub mentions: usize,
    pub sources: BTreeMap<Kind, usize>,
    pub calls: usize,
    pub replayed: usize,
    pub cost: f64,
    pub decisions: Vec<Decision>,
    pub tx: Option<u64>,
    pub written: usize,
    /// Links the model chose that a review has taken back: never written again.
    pub rejected: Vec<String>,
}

fn label(store: &Store, t: u32, id: u64, as_of: u64) -> Result<Option<(String, i64)>> {
    for e in store.edges(t, id, Dir::Out, as_of, None, &mut ScanCost::default())? {
        if e.pred == Pred::Label {
            return Ok(Some((store.name(t, e.other)?.trim_start_matches("lit:").to_string(), e.valid_from)));
        }
    }
    Ok(None)
}

/// Every source with a mention not yet turned into a link, with all its mentions: a source
/// is always asked about everything it names, so its request, and its recording, stays the
/// same however many of its links are already written.
pub fn candidates(store: &Store, t: u32) -> Result<BTreeMap<String, (u64, Vec<(String, u64)>)>> {
    let head = store.head(t)?;
    let mut cost = ScanCost::default();
    let mut typed = std::collections::HashSet::new();
    for p in WRITES {
        for (s, o, _) in store.by_pred(t, *p, head, &mut cost)? {
            typed.insert((s, o));
        }
    }
    let mut by_source: BTreeMap<String, (u64, Vec<(String, u64)>)> = BTreeMap::new();
    let mut open = std::collections::HashSet::new();
    for (s, o, _) in store.by_pred(t, Pred::Mentions, head, &mut cost)? {
        let (sn, on) = (store.name(t, s)?, store.name(t, o)?);
        if options(Kind::of(&sn).unwrap(), Kind::of(&on).unwrap(), "x").is_empty() {
            continue;
        }
        if !typed.contains(&(s, o)) {
            open.insert(s);
        }
        by_source.entry(sn).or_insert((s, vec![])).1.push((on, o));
    }
    by_source.retain(|_, (s, _)| open.contains(s));
    // By name, so a request, and its recording, does not depend on the order things were ingested.
    by_source.values_mut().for_each(|(_, targets)| targets.sort());
    Ok(by_source)
}

pub fn dream(store: &Store, t: u32, dir: &Path, cfg: &Config, opts: &Opts) -> Result<Report> {
    let head = store.head(t)?;
    let mut model = Model::open(dir, cfg)?;
    let mut report = Report { dry_run: opts.dry_run, to_call: 0, estimate: 0.0, mentions: 0, sources: BTreeMap::new(), calls: 0, replayed: 0, cost: 0.0, decisions: vec![], tx: None, written: 0, rejected: vec![] };
    let mut pending = vec![];
    let mut links = std::collections::HashSet::new();
    for p in WRITES {
        for (s, o, _) in store.by_pred(t, *p, head, &mut ScanCost::default())? {
            links.insert((store.name(t, s)?, *p, store.name(t, o)?));
        }
    }
    for (source, (sid, targets)) in candidates(store, t)? {
        if let Some(since) = opts.since {
            if label(store, t, sid, head)?.is_none_or(|(_, at)| at < since) {
                continue;
            }
        }
        let pointer = store
            .edges(t, sid, Dir::Out, head, None, &mut ScanCost::default())?
            .into_iter()
            .find(|e| e.pred == Pred::Pointer)
            .map(|e| store.name(t, e.other))
            .transpose()?
            .ok_or_else(|| format!("{source} has no pointer to read"))?;
        let evidence = crate::construct::ingest::evidence(dir, pointer.trim_start_matches("lit:"))?;
        let sk = Kind::of(&source).unwrap();
        *report.sources.entry(sk).or_default() += 1;
        let mut questions = vec![];
        for (target, oid) in &targets {
            let id = target.split_once(':').unwrap().1;
            let shown = match label(store, t, *oid, head)? {
                Some((l, _)) => format!("{id} (\"{l}\")"),
                None => id.to_string(),
            };
            questions.push(Choice { instructions: format!("`record` names {shown}. What is `record`'s link to it?"), options: options(sk, Kind::of(target).unwrap(), &shown) });
        }
        report.mentions += questions.len();
        if opts.dry_run {
            let (recorded, dollars) = model.estimate(&evidence, &questions);
            if !recorded {
                report.to_call += 1;
                report.estimate += dollars;
            }
            continue;
        }
        match model.ask(&evidence, &questions)? {
            Outcome::NeedsKey => pending.push(source.clone()),
            Outcome::Answered { answers, replayed, cost } => {
                report.calls += 1;
                report.replayed += replayed as usize;
                if !replayed {
                    report.cost += cost;
                }
                for ((target, _), a) in targets.iter().zip(answers) {
                    let written = Pred::from_name(&a.choice).is_some_and(|p| links.contains(&(source.clone(), p, target.clone())));
                    report.decisions.push(Decision { s: source.clone(), o: target.clone(), choice: a.choice, p: a.p, written });
                }
            }
        }
    }
    if opts.dry_run {
        return Ok(report);
    }
    if !pending.is_empty() {
        return Err(format!("{} sources need the model and no key is set ({}); nothing written. Set {} or run `midb key set`.", pending.len(), pending.join(", "), cfg.model.key_env).into());
    }
    let rejected = crate::construct::review::rejected(store, t)?;
    let mut facts = vec![];
    for d in &report.decisions {
        if d.choice == ONLY || d.p < ACCEPT || d.written {
            continue;
        }
        let link = format!("{} {} {}", d.s, d.choice, d.o);
        if rejected.contains(&link) {
            report.rejected.push(link);
            continue;
        }
        let sid = store.id(t, &d.s)?.unwrap();
        let mut f = FactIn::new(&d.s, Pred::from_name(&d.choice).ok_or_else(|| format!("{}: not a link type", d.choice))?, &d.o, "dream");
        f.valid_from = label(store, t, sid, head)?.map(|(_, at)| at);
        facts.push(f);
    }
    if !facts.is_empty() {
        report.written = facts.len();
        report.tx = Some(store.write(t, &facts)?);
    }
    Ok(report)
}
