//! WALK: P8QL (specs/p8ql.md). A SQL-like statement whose every clause is one native step:
//! `FROM … LIKE` is a likeness step, each arrow in `WALK` is one connection step (a prefix
//! scan), and `WALK FROM … FOLLOW` is the native walk. `explain` returns the plan without
//! running it; `run` runs it and reports each step's rows and keys read. The plan runs in the
//! order the statement is written: there is no planner, only refusals and path expansion.

use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::time::Instant;

use crate::model::{Kind, Pred};
use crate::store::{Dir, ScanCost, Store};
use crate::Result;

use super::{search, session};

// ---------------------------------------------------------------------------------------
// Lexing

#[derive(Clone, Debug, PartialEq)]
enum Tok {
    Word(String),
    Str(String),
    Num(f64),
    /// `-pred->`
    Out(String),
    /// `<-pred-`
    In(String),
    /// `-[path]-`
    Path(String),
    Sym(&'static str),
}

fn lex(src: &str) -> Result<Vec<Tok>> {
    let c: Vec<char> = src.chars().collect();
    let mut out = vec![];
    let mut i = 0;
    let ident = |i: &mut usize| -> String {
        let s = *i;
        while *i < c.len() && (c[*i].is_alphanumeric() || c[*i] == '_') {
            *i += 1;
        }
        c[s..*i].iter().collect()
    };
    while i < c.len() {
        let ch = c[i];
        if ch.is_whitespace() {
            i += 1;
        } else if ch == '-' && c.get(i + 1) == Some(&'-') {
            while i < c.len() && c[i] != '\n' {
                i += 1;
            }
        } else if ch == '\'' {
            let s = i + 1;
            i = s;
            while i < c.len() && c[i] != '\'' {
                i += 1;
            }
            if i == c.len() {
                return Err("a string is not closed with '".into());
            }
            out.push(Tok::Str(c[s..i].iter().collect()));
            i += 1;
        } else if ch == '<' && c.get(i + 1) == Some(&'-') {
            i += 2;
            let p = ident(&mut i);
            if p.is_empty() || c.get(i) != Some(&'-') {
                return Err(format!("`<-{p}` must close with `-`, as in <-authoredBy-").into());
            }
            i += 1;
            out.push(Tok::In(p));
        } else if ch == '<' && c.get(i + 1) == Some(&'>') {
            i += 2;
            out.push(Tok::Sym("<>"));
        } else if ch == '-' && c.get(i + 1) == Some(&'[') {
            i += 2;
            let p = ident(&mut i);
            if c.get(i) != Some(&']') || c.get(i + 1) != Some(&'-') {
                return Err(format!("`-[{p}` must close with `]-`, as in -[works_with]-").into());
            }
            i += 2;
            out.push(Tok::Path(p));
        } else if ch == '-' && c.get(i + 1).is_some_and(|x| x.is_alphabetic()) {
            i += 1;
            let p = ident(&mut i);
            if c.get(i) != Some(&'-') || c.get(i + 1) != Some(&'>') {
                return Err(format!("`-{p}` must close with `->`, as in -touches->").into());
            }
            i += 2;
            out.push(Tok::Out(p));
        } else if ch.is_ascii_digit() {
            let s = i;
            while i < c.len() && (c[i].is_ascii_digit() || c[i] == '.') {
                i += 1;
            }
            let t: String = c[s..i].iter().collect();
            out.push(Tok::Num(t.parse().map_err(|_| format!("{t}: not a number"))?));
        } else if ch.is_alphabetic() || ch == '_' {
            out.push(Tok::Word(ident(&mut i)));
        } else {
            let sym = match ch {
                ',' => ",",
                ';' => ";",
                '(' => "(",
                ')' => ")",
                '*' => "*",
                '=' => "=",
                _ => return Err(format!("unexpected `{ch}`").into()),
            };
            out.push(Tok::Sym(sym));
            i += 1;
        }
    }
    Ok(out)
}

// ---------------------------------------------------------------------------------------
// The statement

#[derive(Clone, Debug)]
pub enum Start {
    Exact(String),
    Like(String),
}

#[derive(Clone, Debug)]
pub struct Hop {
    pub dir: Dir,
    pub pred: Pred,
    pub kind: String,
    /// The named path this hop came from, if any.
    pub path: Option<String>,
}

#[derive(Clone, Debug)]
pub enum Item {
    All,
    Var(String),
    /// count(*) or count(DISTINCT kind), with its alias
    Count { distinct: Option<String>, alias: String },
}

#[derive(Clone, Debug, Default)]
pub struct Select {
    pub items: Vec<Item>,
    pub kind: String,
    pub start: Option<Start>,
    pub from_var: String,
    pub hops: Vec<Hop>,
    pub walk_var: Option<String>,
    /// `a <> b` or `a <> 'node'`
    pub not_equal: Vec<(String, String)>,
    pub group_by: Option<String>,
    pub order_by: Option<(String, bool)>,
    pub limit: Option<usize>,
    pub as_of: Option<u64>,
}

#[derive(Clone, Debug)]
pub struct WalkFrom {
    pub from: Select,
    pub follow: Vec<(String, f64)>,
    pub budget: usize,
}

#[derive(Clone, Debug)]
pub enum Stmt {
    Select(Select),
    Walk(WalkFrom),
}

struct P<'a> {
    t: Vec<Tok>,
    i: usize,
    paths: &'a BTreeMap<String, String>,
}

impl P<'_> {
    fn peek(&self) -> Option<&Tok> {
        self.t.get(self.i)
    }
    fn next(&mut self) -> Option<Tok> {
        let t = self.t.get(self.i).cloned();
        self.i += 1;
        t
    }
    fn is_kw(&self, k: &str) -> bool {
        matches!(self.peek(), Some(Tok::Word(w)) if w.eq_ignore_ascii_case(k))
    }
    fn kw(&mut self, k: &str) -> Result<()> {
        if self.is_kw(k) {
            self.i += 1;
            Ok(())
        } else {
            Err(format!("expected {k}, found {}", self.found()).into())
        }
    }
    fn sym(&mut self, s: &str) -> Result<()> {
        if self.peek() == Some(&Tok::Sym(match s {
            "," => ",",
            "(" => "(",
            ")" => ")",
            "*" => "*",
            "=" => "=",
            "<>" => "<>",
            _ => ";",
        })) {
            self.i += 1;
            Ok(())
        } else {
            Err(format!("expected `{s}`, found {}", self.found()).into())
        }
    }
    fn is_sym(&self, s: &str) -> bool {
        matches!(self.peek(), Some(Tok::Sym(x)) if *x == s)
    }
    fn word(&mut self) -> Result<String> {
        match self.next() {
            Some(Tok::Word(w)) => Ok(w),
            t => Err(format!("expected a name, found {}", show(t.as_ref())).into()),
        }
    }
    fn string(&mut self) -> Result<String> {
        match self.next() {
            Some(Tok::Str(s)) => Ok(s),
            t => Err(format!("expected a quoted string, found {}", show(t.as_ref())).into()),
        }
    }
    fn num(&mut self) -> Result<f64> {
        match self.next() {
            Some(Tok::Num(n)) => Ok(n),
            t => Err(format!("expected a number, found {}", show(t.as_ref())).into()),
        }
    }
    fn found(&self) -> String {
        show(self.peek())
    }

    fn stmt(&mut self) -> Result<Stmt> {
        let s = if self.is_kw("WALK") {
            self.i += 1;
            self.kw("FROM")?;
            self.sym("(")?;
            let from = self.select()?;
            self.sym(")")?;
            let mut follow = vec![];
            if self.is_kw("FOLLOW") {
                self.i += 1;
                loop {
                    let p = self.word()?;
                    Pred::from_name(&p).ok_or_else(|| format!("{p}: not a link type"))?;
                    follow.push((p, self.num()?));
                    if !self.is_sym(",") {
                        break;
                    }
                    self.i += 1;
                }
            }
            if self.is_kw("UNTIL") {
                self.i += 1;
                self.kw("frontier")?;
                self.kw("EMPTY")?;
            }
            let mut budget = 20;
            if self.is_kw("BUDGET") {
                self.i += 1;
                budget = self.num()? as usize;
            }
            self.kw("RETURN")?;
            self.kw("PATH")?;
            Stmt::Walk(WalkFrom { from, follow, budget })
        } else {
            Stmt::Select(self.select()?)
        };
        if self.is_sym(";") {
            self.i += 1;
        }
        if self.peek().is_some() {
            return Err(format!("unexpected {} after the statement", self.found()).into());
        }
        Ok(s)
    }

    fn select(&mut self) -> Result<Select> {
        let mut q = Select::default();
        self.kw("SELECT")?;
        loop {
            if self.is_sym("*") {
                self.i += 1;
                q.items.push(Item::All);
            } else if self.is_kw("count") {
                self.i += 1;
                self.sym("(")?;
                let distinct = if self.is_sym("*") {
                    self.i += 1;
                    None
                } else {
                    self.kw("DISTINCT")?;
                    Some(self.word()?)
                };
                self.sym(")")?;
                self.kw("AS")?;
                q.items.push(Item::Count { distinct, alias: self.word()? });
            } else {
                q.items.push(Item::Var(self.word()?));
            }
            if !self.is_sym(",") {
                break;
            }
            self.i += 1;
        }
        self.kw("FROM")?;
        q.kind = self.word()?;
        if self.is_kw("LIKE") {
            self.i += 1;
            q.start = Some(Start::Like(self.string()?));
        } else if self.is_sym("=") {
            self.i += 1;
            q.start = Some(Start::Exact(self.string()?));
        }
        q.from_var = if self.is_kw("AS") {
            self.i += 1;
            self.word()?
        } else {
            q.kind.clone()
        };
        if self.is_kw("WALK") {
            self.i += 1;
            let v = self.word()?;
            if v != q.from_var {
                return Err(format!("WALK starts at {v}, but FROM names {}", q.from_var).into());
            }
            loop {
                let (dir, pred, path) = match self.next() {
                    Some(Tok::Out(p)) => (Dir::Out, p, None),
                    Some(Tok::In(p)) => (Dir::In, p, None),
                    Some(Tok::Path(name)) => (Dir::Out, String::new(), Some(name)),
                    t => return Err(format!("expected a hop such as -touches-> or <-authoredBy-, found {}", show(t.as_ref())).into()),
                };
                let kind = self.word()?;
                match path {
                    None => q.hops.push(Hop { dir, pred: pred_named(&pred)?, kind, path: None }),
                    Some(name) => q.hops.extend(expand(self.paths, &name, &kind)?),
                }
                if !matches!(self.peek(), Some(Tok::Out(_) | Tok::In(_) | Tok::Path(_))) {
                    break;
                }
            }
            self.kw("AS")?;
            q.walk_var = Some(self.word()?);
        }
        if self.is_kw("WHERE") {
            self.i += 1;
            loop {
                let a = self.word()?;
                self.sym("<>")?;
                let b = match self.next() {
                    Some(Tok::Word(w)) => w,
                    Some(Tok::Str(s)) => format!("'{s}"),
                    t => return Err(format!("expected a name or a quoted record, found {}", show(t.as_ref())).into()),
                };
                q.not_equal.push((a, b));
                if !self.is_kw("AND") {
                    break;
                }
                self.i += 1;
            }
        }
        if self.is_kw("AS") {
            self.i += 1;
            self.kw("OF")?;
            let w = self.word()?;
            q.as_of = Some(w.trim_start_matches(['T', 't']).parse().map_err(|_| format!("{w}: want T<n>, a transaction"))?);
        }
        if self.is_kw("GROUP") {
            self.i += 1;
            self.kw("BY")?;
            q.group_by = Some(self.word()?);
        }
        if self.is_kw("ORDER") {
            self.i += 1;
            self.kw("BY")?;
            let k = self.word()?;
            let desc = if self.is_kw("DESC") {
                self.i += 1;
                true
            } else {
                if self.is_kw("ASC") {
                    self.i += 1;
                }
                false
            };
            q.order_by = Some((k, desc));
        }
        if self.is_kw("LIMIT") {
            self.i += 1;
            q.limit = Some(self.num()? as usize);
        }
        Ok(q)
    }
}

fn show(t: Option<&Tok>) -> String {
    match t {
        None => "the end".into(),
        Some(Tok::Word(w)) => format!("`{w}`"),
        Some(Tok::Str(s)) => format!("'{s}'"),
        Some(Tok::Num(n)) => format!("{n}"),
        Some(Tok::Out(p)) => format!("-{p}->"),
        Some(Tok::In(p)) => format!("<-{p}-"),
        Some(Tok::Path(p)) => format!("-[{p}]-"),
        Some(Tok::Sym(s)) => format!("`{s}`"),
    }
}

fn pred_named(p: &str) -> Result<Pred> {
    Ok(Pred::from_name(p).ok_or_else(|| format!("{p}: not a link type (p8ql_schema lists them)"))?)
}

/// A named path's hops, closed by the kind the statement names after it. A path is written
/// as hops with the kinds between them, and ends with an arrow:
/// `<-authoredBy- commit -touches-> file <-touches- commit -authoredBy->`.
fn expand(paths: &BTreeMap<String, String>, name: &str, last: &str) -> Result<Vec<Hop>> {
    let def = paths.get(name).ok_or_else(|| format!("{name}: no such path (define it under [paths] in avalanche.toml)"))?;
    let toks = lex(def)?;
    let mut hops = vec![];
    let mut i = 0;
    while i < toks.len() {
        let (dir, p) = match &toks[i] {
            Tok::Out(p) => (Dir::Out, p),
            Tok::In(p) => (Dir::In, p),
            t => return Err(format!("path {name}: expected a hop, found {}", show(Some(t))).into()),
        };
        let kind = match toks.get(i + 1) {
            Some(Tok::Word(k)) => k.clone(),
            None => last.to_string(),
            Some(t) => return Err(format!("path {name}: expected a kind, found {}", show(Some(t))).into()),
        };
        hops.push(Hop { dir, pred: pred_named(p)?, kind, path: Some(name.to_string()) });
        i += 2;
    }
    if hops.is_empty() {
        return Err(format!("path {name} has no hops").into());
    }
    Ok(hops)
}

pub fn parse(src: &str, paths: &BTreeMap<String, String>) -> Result<Stmt> {
    P { t: lex(src)?, i: 0, paths }.stmt()
}

// ---------------------------------------------------------------------------------------
// Type checks: a hop that cannot exist is refused before anything runs

fn kind_of(k: &str) -> Result<Option<Kind>> {
    if k == "record" {
        return Ok(None);
    }
    Kind::of(&format!("{k}:x")).map(Some).ok_or_else(|| format!("{k}: not a kind (p8ql_schema lists them)").into())
}

fn check(q: &Select) -> Result<()> {
    let mut at = kind_of(&q.kind)?;
    for h in &q.hops {
        let to = kind_of(&h.kind)?;
        let (dom, rng) = h.pred.signature();
        // -p-> reads from a subject to an object; <-p- from an object back to its subject.
        let (from_side, to_side) = if h.dir == Dir::Out { (dom, rng) } else { (rng, dom) };
        let arrow = arrow(h);
        if let Some(a) = at {
            if !from_side.contains(&a) {
                return Err(format!("{arrow} cannot start at a {} ({} links {} to {})", kname(a), h.pred.name(), kinds(dom), kinds(rng)).into());
            }
        }
        if let Some(b) = to {
            if !to_side.contains(&b) {
                return Err(format!("{arrow} cannot reach a {} ({} links {} to {})", h.kind, h.pred.name(), kinds(dom), kinds(rng)).into());
            }
        }
        at = to;
    }
    Ok(())
}

fn n_rows(n: usize) -> String {
    format!("{n} row{}", if n == 1 { "" } else { "s" })
}

fn kname(k: Kind) -> String {
    format!("{k:?}").to_lowercase()
}

fn kinds(ks: &[Kind]) -> String {
    if ks.len() > 6 {
        return "most kinds".into();
    }
    ks.iter().map(|k| kname(*k)).collect::<Vec<_>>().join("|")
}

fn arrow(h: &Hop) -> String {
    if h.dir == Dir::Out { format!("-{}->", h.pred.name()) } else { format!("<-{}-", h.pred.name()) }
}

// ---------------------------------------------------------------------------------------
// The plan

pub struct Plan {
    pub as_of: u64,
    pub head: u64,
    pub steps: Vec<String>,
}

impl std::fmt::Display for Plan {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        writeln!(f, "plan  T{}{}", self.as_of, if self.as_of < self.head { format!(" of T{}", self.head) } else { String::new() })?;
        for (i, s) in self.steps.iter().enumerate() {
            writeln!(f, "  {:<2} {s}", i + 1)?;
        }
        Ok(())
    }
}

fn start_step(q: &Select) -> String {
    match &q.start {
        Some(Start::Exact(id)) => format!("{:<8} {:<34} dict, one key", "lookup", exact_name(&q.kind, id)),
        Some(Start::Like(w)) if is_name_like(w) => format!("{:<8} {:<34} names and labels of kind {}, fuzzy", "like", format!("{} '{w}'", q.kind), q.kind),
        Some(Start::Like(w)) => format!("{:<8} {:<34} label search (BM25){}", "like", format!("{} '{}'", q.kind, crate::model::short(w, 24)), if q.kind == "record" { String::new() } else { format!(", kind {}", q.kind) }),
        None => format!("{:<8} {:<34} psog, every {} with a label", "scan", q.kind, q.kind),
    }
}

fn hop_steps(q: &Select) -> Vec<String> {
    let mut out = vec![];
    for h in &q.hops {
        let scan = if h.dir == Dir::Out { "spog" } else { "ospg" };
        let via = h.path.as_ref().map(|p| format!("  (path {p})")).unwrap_or_default();
        out.push(format!("{:<8} {:<34} {scan} prefix scan per row{via}", "hop", format!("{} {}", arrow(h), h.kind)));
    }
    for (a, b) in &q.not_equal {
        out.push(format!("{:<8} {a} <> {}", "filter", b.trim_start_matches('\'')));
    }
    if q.items.iter().any(|i| matches!(i, Item::Count { .. })) {
        let what: Vec<String> = q.items.iter().filter_map(|i| match i {
            Item::Count { distinct: Some(k), .. } => Some(format!("count(distinct {k})")),
            Item::Count { distinct: None, .. } => Some("count(*)".into()),
            _ => None,
        }).collect();
        out.push(format!("{:<8} {}{}", "group", q.group_by.as_deref().map(|g| format!("{g}, ")).unwrap_or_default(), what.join(", ")));
    }
    if q.items.iter().any(|i| matches!(i, Item::All)) && q.hops.is_empty() {
        out.push(format!("{:<8} {:<34} spog + ospg prefix scans", "edges", "out, in"));
    }
    if let Some((k, d)) = &q.order_by {
        out.push(format!("{:<8} {k}{}", "order", if *d { " desc" } else { "" }));
    }
    if let Some(n) = q.limit {
        out.push(format!("{:<8} {n}", "limit"));
    }
    out
}

/// A single word is a name to match fuzzily; several words are a question to search.
fn is_name_like(w: &str) -> bool {
    w.split_whitespace().count() == 1
}

fn exact_name(kind: &str, id: &str) -> String {
    if id.contains(':') || kind == "record" { id.to_string() } else { format!("{kind}:{id}") }
}

pub fn explain(store: &Store, t: u32, stmt: &Stmt) -> Result<Plan> {
    let head = store.head(t)?;
    Ok(match stmt {
        Stmt::Select(q) => {
            check(q)?;
            let mut steps = vec![start_step(q)];
            steps.extend(hop_steps(q));
            Plan { as_of: q.as_of.unwrap_or(head).min(head), head, steps }
        }
        Stmt::Walk(w) => {
            check(&w.from)?;
            let policy = if w.follow.is_empty() { "the default policy".to_string() } else { w.follow.iter().map(|(p, x)| format!("{p} {x}")).collect::<Vec<_>>().join(", ") };
            let steps = vec![
                format!("{} → the top record", start_step(&w.from)),
                format!("{:<8} {:<34} follow {policy}; others 0", "frontier", format!("budget {}", w.budget)),
                format!("{:<8} {:<34} until the frontier is empty or the budget runs out", "step…", "best open question each step"),
            ];
            Plan { as_of: w.from.as_of.unwrap_or(head).min(head), head, steps }
        }
    })
}

// ---------------------------------------------------------------------------------------
// Running it

/// How far apart the top two candidates of a LIKE must be for it to carry the first one
/// forward. Closer than this, the query pauses and returns the candidates instead.
pub const CLOSE: f64 = 0.1;

pub struct Candidate {
    pub node: String,
    pub label: String,
    pub score: f64,
}

fn lev(a: &str, b: &str) -> usize {
    let (a, b): (Vec<char>, Vec<char>) = (a.chars().collect(), b.chars().collect());
    let mut prev: Vec<usize> = (0..=b.len()).collect();
    for (i, ca) in a.iter().enumerate() {
        let mut cur = vec![i + 1];
        for (j, cb) in b.iter().enumerate() {
            cur.push((prev[j] + usize::from(ca != cb)).min(prev[j + 1] + 1).min(cur[j] + 1));
        }
        prev = cur;
    }
    prev[b.len()]
}

/// Edit-distance likeness of a word to the best-matching word of a name or label, 0..1.
fn fuzzy(q: &str, text: &str) -> f64 {
    let q = q.to_lowercase();
    text.to_lowercase()
        .split(|c: char| !c.is_alphanumeric())
        .filter(|w| !w.is_empty())
        .map(|w| 1.0 - lev(&q, w) as f64 / q.chars().count().max(w.chars().count()) as f64)
        .fold(0.0, f64::max)
}

/// The likeness step: fuzzy over names and labels for one word, label search for several.
pub fn like(store: &Store, t: u32, kind: &str, words: &str, as_of: u64, cost: &mut ScanCost) -> Result<Vec<Candidate>> {
    let want = kind_of(kind)?;
    let mut out = vec![];
    if is_name_like(words) {
        let prefix = if kind == "record" { String::new() } else { format!("{kind}:") };
        for (name, id) in store.names_with_prefix(t, &prefix)? {
            cost.keys_read += 1;
            let Some(k) = Kind::of(&name) else { continue };
            if matches!(k, Kind::Lit | Kind::Session | Kind::Step | Kind::Review) || want.is_some_and(|w| w != k) {
                continue;
            }
            let label = session::label(store, t, id, as_of, None, cost)?.map(|l| l.0).unwrap_or_default();
            let tail = name.split_once(':').map(|x| x.1).unwrap_or(&name);
            let score = fuzzy(words, tail).max(fuzzy(words, &label));
            if score >= 0.5 && live(store, t, id, as_of, cost)? {
                out.push(Candidate { node: name, label, score });
            }
        }
    } else {
        let hits = search::search(store, t, words, as_of, None)?;
        let top = hits.iter().filter(|h| want.is_none() || Kind::of(&h.node) == want).map(|h| h.score).fold(0.0, f64::max);
        for h in hits {
            if want.is_none() || Kind::of(&h.node) == want {
                out.push(Candidate { score: h.score / top, node: h.node, label: h.label });
            }
        }
    }
    out.sort_by(|a, b| b.score.total_cmp(&a.score).then(a.node.cmp(&b.node)));
    Ok(out)
}

/// A name in the dictionary may have had all its facts retracted, or arrived after T.
fn live(store: &Store, t: u32, id: u64, as_of: u64, cost: &mut ScanCost) -> Result<bool> {
    Ok(!store.edges(t, id, Dir::Out, as_of, None, cost)?.is_empty() || !store.edges(t, id, Dir::In, as_of, None, cost)?.is_empty())
}

pub enum Outcome {
    /// The rows, as text, with one line per step run.
    Done(String),
    /// A LIKE found close candidates: choose one with `= '<name>'` and run again.
    Paused(String),
}

pub fn run(store: &Store, t: u32, stmt: &Stmt) -> Result<Outcome> {
    let plan = explain(store, t, stmt)?;
    let clock = Instant::now();
    let mut cost = ScanCost::default();
    let q = match stmt {
        Stmt::Select(q) => q,
        Stmt::Walk(w) => &w.from,
    };
    let mut trace = vec![];
    // Step 1: where to start.
    let starts: Vec<u64> = match &q.start {
        Some(Start::Exact(id)) => {
            let name = exact_name(&q.kind, id);
            let n = store.id(t, &name)?.filter(|n| live(store, t, *n, plan.as_of, &mut cost).unwrap_or(false)).ok_or_else(|| format!("{name} is not in the store at T{}", plan.as_of))?;
            trace.push(format!("lookup   {name}"));
            vec![n]
        }
        Some(Start::Like(w)) => {
            let c = like(store, t, &q.kind, w, plan.as_of, &mut cost)?;
            let Some(top) = c.first() else {
                return Ok(Outcome::Done(format!("{plan}  1  like     nothing of kind {} is like '{w}'\nno rows\n", q.kind)));
            };
            if c.len() > 1 && top.score - c[1].score < CLOSE {
                let mut s = format!("{plan}paused at step 1: '{w}' is like {} records about equally; choose one with {} = '<name>' and run again\n", c.iter().take_while(|x| top.score - x.score < CLOSE).count(), q.kind);
                for x in c.iter().take(5) {
                    s += &format!("  {:<28} {:.2}  \"{}\"\n", x.node, x.score, crate::model::short(&x.label, 50));
                }
                return Ok(Outcome::Paused(s));
            }
            trace.push(format!("like     '{w}' → {} {:.2}{}", top.node, top.score, if c.len() > 1 { format!(" (next {} {:.2})", c[1].node, c[1].score) } else { String::new() }));
            vec![store.id(t, &top.node)?.ok_or("a candidate vanished")?]
        }
        None => {
            let pairs = store.by_pred(t, Pred::Label, plan.as_of, &mut cost)?;
            let want = kind_of(&q.kind)?;
            let mut v: Vec<u64> = vec![];
            for (s, _, _) in pairs {
                if want.is_none() || Kind::of(&store.name(t, s)?) == want {
                    v.push(s);
                }
            }
            trace.push(format!("scan     {} {}", v.len(), q.kind));
            v
        }
    };
    if let Stmt::Walk(w) = stmt {
        let start = store.name(t, starts[0])?;
        let mut prefer: Vec<(String, f64)> = vec![];
        if !w.follow.is_empty() {
            for k in session::default_policy().keys() {
                if !w.follow.iter().any(|(p, _)| p == k) {
                    prefer.push((k.clone(), 0.0));
                }
            }
            prefer.extend(w.follow.iter().cloned());
        }
        let s = session::walk(store, t, &start, w.budget, Some(plan.as_of), None, &prefer)?;
        return Ok(Outcome::Done(format!("{plan}ran\n  1  {}\n  2  walk     session {}, {} steps\n{}", trace[0], s.id, s.step, session::why(store, &s, None)?)));
    }
    // Hops: each row is the node sequence so far.
    let mut rows: Vec<Vec<u64>> = starts.into_iter().map(|n| vec![n]).collect();
    let mut kinds_at: Vec<String> = vec![q.kind.clone()];
    let mut names: HashMap<u64, String> = HashMap::new();
    let mut name = |store: &Store, id: u64| -> Result<String> {
        if let Some(n) = names.get(&id) {
            return Ok(n.clone());
        }
        let n = store.name(t, id)?;
        names.insert(id, n.clone());
        Ok(n)
    };
    for h in &q.hops {
        let before = cost.keys_read;
        let want = kind_of(&h.kind)?;
        let mut next = BTreeSet::new();
        for r in &rows {
            for e in store.edges(t, *r.last().unwrap(), h.dir, plan.as_of, None, &mut cost)? {
                if e.pred != h.pred || (want.is_some() && Kind::of(&name(store, e.other)?) != want) {
                    continue;
                }
                let mut r2 = r.clone();
                r2.push(e.other);
                next.insert(r2);
            }
        }
        rows = next.into_iter().collect();
        kinds_at.push(h.kind.clone());
        trace.push(format!("{:<8} {:<34} {}, {} keys", "hop", format!("{} {}", arrow(h), h.kind), n_rows(rows.len()), cost.keys_read - before));
    }
    let var_at = |v: &str| -> Result<usize> {
        if v == q.from_var {
            Ok(0)
        } else if q.walk_var.as_deref() == Some(v) {
            Ok(q.hops.len())
        } else {
            Err(format!("{v}: not named by FROM … AS or WALK … AS").into())
        }
    };
    for (a, b) in &q.not_equal {
        let ia = var_at(a)?;
        let before = rows.len();
        if let Some(lit) = b.strip_prefix('\'') {
            let other = store.id(t, &exact_name(&kinds_at[ia], lit))?;
            rows.retain(|r| Some(r[ia]) != other);
        } else {
            let ib = var_at(b)?;
            rows.retain(|r| r[ia] != r[ib]);
        }
        trace.push(format!("filter   {a} <> {}: {} of {before} kept", b.trim_start_matches('\''), rows.len()));
    }
    // The answer.
    let mut out = String::new();
    let has_count = q.items.iter().any(|i| matches!(i, Item::Count { .. }));
    let mut table: Vec<Vec<String>> = vec![];
    let mut header: Vec<String> = vec![];
    if q.items.iter().any(|i| matches!(i, Item::All)) && q.hops.is_empty() {
        for r in rows.iter().take(q.limit.unwrap_or(usize::MAX)) {
            let n = r[0];
            let me = name(store, n)?;
            let label = session::label(store, t, n, plan.as_of, None, &mut cost)?.map(|l| l.0).unwrap_or_default();
            out += &format!("{me}  \"{label}\"\n");
            for dir in [Dir::Out, Dir::In] {
                for e in store.edges(t, n, dir, plan.as_of, None, &mut cost)? {
                    if e.pred.is_attribute() {
                        continue;
                    }
                    let a = if dir == Dir::Out { format!("-{}->", e.pred.name()) } else { format!("<-{}-", e.pred.name()) };
                    out += &format!("  {a:<16} {:<28} T{}  valid from {}\n", name(store, e.other)?, e.tx, crate::model::date::show(e.valid_from).split(' ').next().unwrap_or(""));
                }
            }
        }
        trace.push("edges    out, in".into());
    } else if has_count {
        let g = q.group_by.as_deref().map(var_at).transpose()?;
        let mut groups: BTreeMap<Option<u64>, Vec<&Vec<u64>>> = BTreeMap::new();
        for r in &rows {
            groups.entry(g.map(|i| r[i])).or_default().push(r);
        }
        for i in &q.items {
            header.push(match i {
                Item::Var(v) => v.clone(),
                Item::Count { alias, .. } => alias.clone(),
                Item::All => "*".into(),
            });
        }
        for (key, rs) in &groups {
            let mut line = vec![];
            for i in &q.items {
                line.push(match i {
                    Item::Var(v) => {
                        let at = var_at(v)?;
                        if Some(at) != g {
                            return Err(format!("{v} must be the GROUP BY name to be selected beside a count").into());
                        }
                        name(store, key.unwrap())?
                    }
                    Item::Count { distinct: None, .. } => rs.len().to_string(),
                    Item::Count { distinct: Some(k), .. } => {
                        let at = kinds_at.iter().position(|x| x == k).ok_or_else(|| format!("count(DISTINCT {k}): no {k} on the walk"))?;
                        rs.iter().map(|r| r[at]).collect::<BTreeSet<_>>().len().to_string()
                    }
                    Item::All => return Err("* cannot be selected beside a count".into()),
                });
            }
            table.push(line);
        }
        trace.push(format!("group    {} groups", groups.len()));
    } else {
        let cols: Vec<usize> = q.items.iter().map(|i| match i {
            Item::Var(v) => var_at(v),
            _ => Ok(q.hops.len()),
        }).collect::<Result<_>>()?;
        for i in &q.items {
            header.push(match i {
                Item::Var(v) => v.clone(),
                _ => q.walk_var.clone().unwrap_or_else(|| q.from_var.clone()),
            });
        }
        let mut seen = BTreeSet::new();
        for r in &rows {
            let key: Vec<u64> = cols.iter().map(|c| r[*c]).collect();
            if seen.insert(key.clone()) {
                table.push(key.iter().map(|n| name(store, *n)).collect::<Result<_>>()?);
            }
        }
    }
    if !header.is_empty() {
        if let Some((k, desc)) = &q.order_by {
            let at = header.iter().position(|h| h == k).ok_or_else(|| format!("ORDER BY {k}: not a selected name"))?;
            table.sort_by(|a, b| {
                let o = match (a[at].parse::<f64>(), b[at].parse::<f64>()) {
                    (Ok(x), Ok(y)) => x.total_cmp(&y),
                    _ => a[at].cmp(&b[at]),
                };
                (if *desc { o.reverse() } else { o }).then(a.cmp(b))
            });
        }
        if let Some(n) = q.limit {
            table.truncate(n);
        }
        let widths: Vec<usize> = (0..header.len()).map(|i| table.iter().map(|r| r[i].chars().count()).chain([header[i].len()]).max().unwrap_or(0)).collect();
        let fmt = |r: &[String]| r.iter().zip(&widths).map(|(c, w)| format!("{c:<w$}")).collect::<Vec<_>>().join("  ").trim_end().to_string();
        out += &format!("{}\n", fmt(&header));
        for r in &table {
            out += &format!("{}\n", fmt(r));
        }
        out += &format!("{}; {} keys read in {:.1?}\n", n_rows(table.len()), cost.keys_read, clock.elapsed());
    } else {
        out += &format!("{} keys read in {:.1?}\n", cost.keys_read, clock.elapsed());
    }
    let mut ran = format!("{plan}ran\n");
    for (i, s) in trace.iter().enumerate() {
        ran += &format!("  {:<2} {s}\n", i + 1);
    }
    Ok(Outcome::Done(ran + &out))
}

/// What a query can name: kinds with their counts, link types with the kinds they join,
/// and the named paths.
pub fn schema(store: &Store, t: u32, paths: &BTreeMap<String, String>) -> Result<String> {
    let head = store.head(t)?;
    let mut cost = ScanCost::default();
    let mut counts: BTreeMap<String, usize> = BTreeMap::new();
    for (name, id) in store.names_with_prefix(t, "")? {
        let Some(k) = Kind::of(&name) else { continue };
        if matches!(k, Kind::Lit | Kind::Session | Kind::Step | Kind::Review) || !live(store, t, id, head, &mut cost)? {
            continue;
        }
        *counts.entry(kname(k)).or_default() += 1;
    }
    let mut s = format!("kinds at T{head}\n");
    for (k, n) in &counts {
        s += &format!("  {k:<10} {n}\n");
    }
    s += "links\n";
    for p in Pred::ALL {
        if p.is_attribute() || matches!(p, Pred::Asked | Pred::InSession | Pred::Visited | Pred::Via) {
            continue;
        }
        let (d, r) = p.signature();
        let used = store.by_pred(t, *p, head, &mut cost)?.len();
        if used > 0 {
            s += &format!("  {:<12} {} -> {}  ({used})\n", p.name(), kinds(d), kinds(r));
        }
    }
    s += "paths\n";
    if paths.is_empty() {
        s += "  none (define them under [paths] in avalanche.toml)\n";
    }
    for (k, v) in paths {
        s += &format!("  {k:<12} {v}\n");
    }
    Ok(s)
}
