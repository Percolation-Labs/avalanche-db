//! The type system. A node's kind is the prefix of its name (`commit:4f2a…`,
//! `card:REM-1172`, `lit:open`), and every predicate names the kinds it may join.
//! A model may propose anything while extracting; only facts that fit here are written.

use serde::Deserialize;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Kind {
    Commit,
    Person,
    File,
    Card,
    Question,
    Claim,
    Package,
    Source,
    Session,
    Step,
    Decision,
    Proposal,
    Issue,
    Pr,
    Lit,
}

impl Kind {
    /// The node prefix an `[ids]` table entry names.
    pub fn prefix(name: &str) -> Option<&'static str> {
        Some(match name {
            "decision" => "decision",
            "proposal" => "proposal",
            "issue" => "issue",
            "card" => "card",
            "question" => "question",
            "claim" => "claim",
            _ => return None,
        })
    }

    pub fn of(name: &str) -> Option<Kind> {
        let (prefix, rest) = name.split_once(':')?;
        if rest.is_empty() {
            return None;
        }
        Some(match prefix {
            "commit" => Kind::Commit,
            "person" => Kind::Person,
            "file" => Kind::File,
            "card" => Kind::Card,
            "question" => Kind::Question,
            "claim" => Kind::Claim,
            "package" => Kind::Package,
            "source" => Kind::Source,
            "session" => Kind::Session,
            "step" => Kind::Step,
            "decision" => Kind::Decision,
            "proposal" => Kind::Proposal,
            "issue" => Kind::Issue,
            "pr" => Kind::Pr,
            "lit" => Kind::Lit,
            _ => return None,
        })
    }
}

use Kind::*;

const THINGS: &[Kind] = &[Commit, Person, File, Card, Question, Claim, Package, Source, Session, Step, Decision, Proposal, Issue, Pr];
/// What a commit or a note can name.
const NAMEABLE: &[Kind] = &[Commit, File, Card, Decision, Proposal, Issue, Pr];
const NOTES: &[Kind] = &[Decision, Proposal, Issue];

macro_rules! preds {
    ($($v:ident = $n:literal, $name:literal, $dom:expr, $rng:expr;)*) => {
        #[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
        pub enum Pred { $($v = $n),* }
        impl Pred {
            pub const ALL: &'static [Pred] = &[$(Pred::$v),*];
            pub fn name(self) -> &'static str { match self { $(Pred::$v => $name),* } }
            pub fn from_name(s: &str) -> Option<Pred> { match s { $($name => Some(Pred::$v),)* _ => None } }
            pub fn from_id(id: u64) -> Option<Pred> { match id { $($n => Some(Pred::$v),)* _ => None } }
            /// (subject kinds, object kinds)
            pub fn signature(self) -> (&'static [Kind], &'static [Kind]) { match self { $(Pred::$v => ($dom, $rng)),* } }
        }
    };
}

preds! {
    Label = 1, "label", THINGS, &[Lit];
    Pointer = 2, "pointer", THINGS, &[Lit];
    Parent = 3, "parent", &[Commit], &[Commit];
    AuthoredBy = 4, "authoredBy", &[Commit], &[Person];
    Touches = 5, "touches", &[Commit], &[File];
    Mentions = 6, "mentions", &[Commit, Decision, Proposal, Issue, Pr, Card], NAMEABLE;
    State = 7, "state", &[Card], &[Lit];
    Answers = 8, "answers", &[Claim], &[Question];
    Stance = 9, "stance", &[Claim], &[Lit];
    Makes = 10, "makes", &[Package], &[Claim];
    Cites = 11, "cites", &[Claim], &[Source];
    Informs = 12, "informs", &[Claim, Question], &[Card];
    Asked = 13, "asked", &[Session], THINGS;
    InSession = 14, "inSession", &[Step], &[Session];
    Visited = 15, "visited", &[Step], THINGS;
    Returned = 16, "returned", &[Step], &[Lit];
    Via = 17, "via", &[Step], &[Lit];
    Because = 20, "because", &[Decision], &[Issue];
    Rejects = 21, "rejects", &[Decision], &[Proposal];
    Adopts = 22, "adopts", &[Decision], &[Proposal];
    Decides = 23, "decides", &[Decision], &[File];
    Duplicates = 24, "duplicates", NOTES, &[Issue];
    Fixes = 25, "fixes", &[Commit, Pr], &[Issue];
    Implements = 26, "implements", &[Commit, Pr], &[Decision, Card];
    MergedAs = 27, "mergedAs", &[Pr], &[Commit];
    Took = 30, "took", &[Step], &[Lit];
    Prefer = 31, "prefer", &[Step, Session], &[Lit];
}

impl Pred {
    pub fn id(self) -> u64 {
        self as u64
    }

    /// Describes a node rather than leading anywhere, so a walk reports it and does not push it.
    pub fn is_attribute(self) -> bool {
        let (_, range) = self.signature();
        range == [Lit]
    }

    /// How the link reads from its object's side: `BUG-12 <-because- ADR-007` is
    /// "BUG-12 led to ADR-007".
    pub fn inverse(self) -> &'static str {
        match self {
            Pred::Because => "led to",
            Pred::Fixes => "fixed by",
            Pred::Implements => "implemented by",
            Pred::Duplicates => "duplicated by",
            Pred::Rejects => "rejected by",
            Pred::Adopts => "adopted by",
            Pred::Decides => "decided by",
            Pred::Mentions => "mentioned by",
            Pred::Answers => "answered by",
            Pred::Makes => "made by",
            Pred::Informs => "informed by",
            Pred::Cites => "cited by",
            Pred::Touches => "touched by",
            Pred::AuthoredBy => "authored",
            Pred::Parent => "child",
            Pred::MergedAs => "merged from",
            _ => self.name(),
        }
    }

    pub fn check(self, s: &str, o: &str) -> Result<(), String> {
        let (dom, rng) = self.signature();
        let sk = Kind::of(s).ok_or_else(|| format!("{s}: not a typed node name"))?;
        let ok = Kind::of(o).ok_or_else(|| format!("{o}: not a typed node name"))?;
        if !dom.contains(&sk) {
            return Err(format!("{} cannot start at {s} ({sk:?})", self.name()));
        }
        if !rng.contains(&ok) {
            return Err(format!("{} cannot end at {o} ({ok:?})", self.name()));
        }
        Ok(())
    }
}

/// A fact as written by an adapter or a model, by name.
#[derive(Clone, Debug, Deserialize)]
pub struct FactIn {
    pub s: String,
    pub p: String,
    pub o: String,
    pub g: String,
    /// When it became true in the world, unix seconds; defaults to the write time.
    #[serde(default, deserialize_with = "date::opt")]
    pub valid_from: Option<i64>,
    #[serde(default, deserialize_with = "date::opt")]
    pub valid_to: Option<i64>,
    #[serde(default)]
    pub retract: bool,
}

impl FactIn {
    pub fn new(s: impl Into<String>, p: Pred, o: impl Into<String>, g: &str) -> FactIn {
        FactIn { s: s.into(), p: p.name().into(), o: o.into(), g: g.into(), valid_from: None, valid_to: None, retract: false }
    }

    pub fn at(mut self, valid_from: i64) -> FactIn {
        self.valid_from = Some(valid_from);
        self
    }

    pub fn pred(&self) -> Result<Pred, String> {
        let p = Pred::from_name(&self.p).ok_or_else(|| format!("{}: not a predicate", self.p))?;
        p.check(&self.s, &self.o)?;
        if self.g.is_empty() {
            return Err("a fact needs a graph".into());
        }
        Ok(p)
    }
}

pub fn lit(text: &str) -> String {
    let flat: String = text.split_whitespace().collect::<Vec<_>>().join(" ");
    let cut: String = flat.chars().take(120).collect();
    format!("lit:{}", if cut.is_empty() { "-" } else { &cut })
}

pub mod date {
    use serde::{Deserialize, Deserializer};

    /// Days since 1970-01-01 for a proleptic Gregorian date (Howard Hinnant's algorithm).
    fn days(y: i64, m: i64, d: i64) -> i64 {
        let y = if m <= 2 { y - 1 } else { y };
        let era = y.div_euclid(400);
        let yoe = y - era * 400;
        let doy = (153 * (if m > 2 { m - 3 } else { m + 9 }) + 2) / 5 + d - 1;
        let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
        era * 146097 + doe - 719468
    }

    /// `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM[:SS]` (UTC), or bare unix seconds.
    pub fn parse(s: &str) -> Option<i64> {
        if let Ok(n) = s.parse::<i64>() {
            return Some(n);
        }
        let (date, time) = s.split_once(['T', ' ']).unwrap_or((s, "00:00:00"));
        let mut d = date.split('-').map(|x| x.parse::<i64>().ok());
        let (y, m, dd) = (d.next()??, d.next()??, d.next()??);
        let mut t = time.trim_end_matches('Z').split(':').map(|x| x.parse::<i64>().unwrap_or(0));
        let secs = t.next().unwrap_or(0) * 3600 + t.next().unwrap_or(0) * 60 + t.next().unwrap_or(0);
        Some(days(y, m, dd) * 86400 + secs)
    }

    pub fn show(secs: i64) -> String {
        if secs == i64::MAX {
            return "open".into();
        }
        let z = secs.div_euclid(86400) + 719468;
        let era = z.div_euclid(146097);
        let doe = z - era * 146097;
        let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
        let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
        let mp = (5 * doy + 2) / 153;
        let d = doy - (153 * mp + 2) / 5 + 1;
        let m = if mp < 10 { mp + 3 } else { mp - 9 };
        let y = yoe + era * 400 + if m <= 2 { 1 } else { 0 };
        let r = secs.rem_euclid(86400);
        format!("{y:04}-{m:02}-{d:02} {:02}:{:02}Z", r / 3600, r % 3600 / 60)
    }

    pub fn opt<'de, D: Deserializer<'de>>(d: D) -> Result<Option<i64>, D::Error> {
        let v: Option<serde_json::Value> = Option::deserialize(d)?;
        Ok(match v {
            Some(serde_json::Value::Number(n)) => n.as_i64(),
            Some(serde_json::Value::String(s)) => parse(&s),
            _ => None,
        })
    }
}
