//! CONSTRUCT: your own documents as a walkable graph. The `documents` adapter reads a folder, a git repository or a
//! JSON-lines file of passages, cuts it into passages, and writes the graph the walk reads: each passage is an
//! `item:` node with its title (`label`), where its text lives (`pointer`), the terms it holds (`tagged`), the
//! passages beside it (`beside`), the passages nearest it in wording (`near`), and the names it mentions (`named`).
//!
//! Everything here is built from the documents alone, at ingestion, and never from a question: these are the
//! ingestion-time data the D6 door reads (`walk::d6`). As everywhere in the store, no text is copied: a pointer says
//! where a passage's text is, and `Reader::text` reads it back.
//!
//! Construction choices, each a difference from the walk lab's MuSiQue graph that a test must carry:
//!   terms   content words (stop words out, three letters or more, or a four-digit year) and the two-word phrases of adjacent
//!           content words; only those held by two to TERM_MAX_DF passages: a term held once leads nowhere, and one
//!           held by more is never a door
//!   near    the five passages with the highest tf-idf cosine (at least 0.1), not embedding neighbours: the binary
//!           carries no embedding model
//!   beside  the passage before and after in the same file; a commit's parents and children
//!   names   capitalised runs of one to four words that do not open a sentence, and code identifiers (snake_case,
//!           CamelCase, a::b), less those held by more than one passage in twenty

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::process::Command;

use super::ingest::Ingested;
use crate::model::{lit, FactIn, Pred};
use crate::store::Store;
use crate::Result;

/// A passage is cut at about this many characters, on a paragraph or line boundary.
const CHUNK: usize = 1200;
const NEAR: usize = 5;
/// A term held by more passages than this is not stored. The walk opens a term door only when the term is held by at
/// most its `cap` passages (100 by default), so above twice that a term is never a door; on MuSiQue such terms were
/// 62% of the term facts.
pub const TERM_MAX_DF: usize = 200;
const NEAR_MIN: f64 = 0.1;
/// Terms held by more passages than this are not used to find near candidates (they are too common to say much).
const NEAR_DF: usize = 50;
/// A file larger than this is not read.
const MAX_FILE: u64 = 256 * 1024;

const TEXT_EXT: &[&str] = &["md", "markdown", "txt", "rst", "adoc", "org"];
const CODE_EXT: &[&str] = &[
    "rs", "py", "js", "jsx", "ts", "tsx", "go", "java", "kt", "c", "h", "cc", "cpp", "hpp", "cs", "rb", "php", "swift", "scala",
    "sh", "bash", "zsh", "sql", "toml", "yaml", "yml", "ex", "exs", "hs", "ml", "lua", "r", "jl",
];
const SKIP_DIRS: &[&str] = &["node_modules", "target", "vendor", "dist", "build", "__pycache__", ".git", ".avalanche"];

/// Capitalised words that are not names: months, days, and words that open lines of a commit or a comment.
const NOT_NAMES: &[&str] = &[
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec", "january", "february", "march",
    "april", "june", "july", "august", "september", "october", "november", "december", "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday", "todo", "note", "fixme", "see", "every", "each", "returns",
];

pub const STOP: &[&str] = &[
    "a", "about", "above", "after", "again", "against", "all", "also", "am", "an", "and", "any", "are", "as", "at", "be",
    "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "could", "did", "do", "does",
    "doing", "down", "during", "each", "else", "few", "for", "from", "further", "had", "has", "have", "having", "he",
    "her", "here", "hers", "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "may",
    "me", "might", "more", "most", "must", "my", "no", "nor", "not", "now", "of", "off", "on", "once", "one", "only",
    "or", "other", "our", "ours", "out", "over", "own", "same", "shall", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "upon", "us", "use", "used", "uses", "using", "very", "was", "we", "were", "what", "when",
    "where", "which", "while", "who", "whom", "why", "will", "with", "would", "yet", "you", "your", "yours", "let",
    "new", "get", "set", "via", "per", "non", "self", "none", "true", "false", "null", "return", "returns", "fn", "def",
    "pub", "mut", "impl", "struct", "enum", "const", "static", "var", "function", "class", "import", "from", "export",
    "string", "str", "int", "bool", "vec", "option", "result", "some", "ok", "err",
];

/// One passage before it becomes facts.
#[derive(Clone, Debug)]
pub struct Passage {
    pub id: String,
    pub title: String,
    pub text: String,
    pub pointer: String,
    /// The passage it follows, in its file or history.
    pub after: Option<String>,
    pub at: Option<i64>,
}

/// The document's id as a node.
pub fn item(id: &str) -> String {
    format!("item:{id}")
}

/// Lower-case content words, in order: stop words, words under three letters and words opening with a digit out; a
/// four-digit number (a year) kept.
pub fn words(text: &str) -> Vec<String> {
    text.to_lowercase()
        .split(|c: char| !(c.is_alphanumeric() || c == '_'))
        .map(|w| w.trim_matches('_'))
        .filter(|w| {
            let digits = w.chars().all(|c| c.is_ascii_digit());
            !w.is_empty() && !STOP.contains(w) && (if digits { w.len() == 4 } else { w.chars().count() >= 3 && !w.chars().next().is_some_and(|c| c.is_ascii_digit()) })
        })
        .map(String::from)
        .collect()
}

/// The terms a passage holds: its content words and the two-word phrases of adjacent content words in one sentence.
pub fn terms(text: &str) -> BTreeSet<String> {
    let mut out = BTreeSet::new();
    for sentence in text.split(['.', '\n', ';', '!', '?']) {
        let raw: Vec<String> = sentence
            .to_lowercase()
            .split(|c: char| !(c.is_alphanumeric() || c == '_'))
            .map(|w| w.trim_matches('_').to_string())
            .filter(|w| !w.is_empty())
            .collect();
        let keep = |w: &str| words(w).len() == 1;
        for w in &raw {
            if keep(w) {
                out.insert(w.clone());
            }
        }
        for pair in raw.windows(2) {
            if keep(&pair[0]) && keep(&pair[1]) {
                out.insert(format!("{} {}", pair[0], pair[1]));
            }
        }
    }
    out
}

fn is_ident(w: &str) -> bool {
    if w.contains('/') || w.contains("://") || w.contains('<') || w.contains('=') {
        return false;
    }
    let inner = w.trim_matches(|c: char| !c.is_alphanumeric());
    if inner.len() < 4 {
        return false;
    }
    let snake = inner.contains('_') && inner.chars().any(|c| c.is_alphabetic());
    let path = w.contains("::");
    let camel = inner.chars().next().is_some_and(|c| c.is_alphabetic())
        && inner.chars().skip(1).any(|c| c.is_uppercase())
        && inner.chars().any(|c| c.is_lowercase());
    snake || path || camel
}

/// The names a passage mentions: capitalised runs of one to four words that do not open a sentence, and code
/// identifiers. Each once, in order.
pub fn names(text: &str) -> Vec<String> {
    let mut out: Vec<String> = vec![];
    let mut push = |n: String| {
        if !n.is_empty() && !out.contains(&n) {
            out.push(n);
        }
    };
    for sentence in text.split(['.', '\n', ';', '!', '?', ':', '(', ')', '[', ']', '"']) {
        // tokens with no letter or digit (`#`, `//!`, `-`) are not words, so the word after them still opens the line
        let toks: Vec<&str> = sentence.split_whitespace().filter(|t| t.chars().any(char::is_alphanumeric)).collect();
        let mut run: Vec<&str> = vec![];
        for (i, raw) in toks.iter().enumerate() {
            if is_ident(raw) {
                push(raw.trim_matches(|c: char| !(c.is_alphanumeric() || c == '_' || c == ':')).trim_end_matches(':').to_string());
            }
            let w = raw.trim_matches(|c: char| !c.is_alphanumeric());
            let lower = w.to_lowercase();
            let cap = w.chars().next().is_some_and(|c| c.is_uppercase())
                && w.chars().count() >= 2
                && !raw.contains('/')
                && !STOP.contains(&lower.as_str())
                && !NOT_NAMES.contains(&lower.as_str());
            if cap && (i > 0 || !run.is_empty()) && run.len() < 4 {
                run.push(w);
            } else {
                if !run.is_empty() {
                    push(run.join(" "));
                }
                run.clear();
            }
            if raw.ends_with(',') && !run.is_empty() {
                push(run.join(" "));
                run.clear();
            }
        }
        if !run.is_empty() {
            push(run.join(" "));
        }
    }
    out
}

/// A passage's text without what its title already says: leading markdown headings, and a first line the title
/// carries (a commit's subject).
pub fn body(title: &str, text: &str) -> String {
    let mut lines = text.lines().skip_while(|l| l.trim().is_empty() || l.trim_start().starts_with('#')).peekable();
    // the stored title is cut at 120 characters, so a long subject is matched on its opening
    let opens = |l: &str| title.contains(&l.trim().chars().take(40).collect::<String>());
    if lines.peek().is_some_and(|l| !l.trim().is_empty() && opens(l)) {
        lines.next();
    }
    let rest = lines.collect::<Vec<_>>().join("\n");
    if rest.trim().is_empty() { text.to_string() } else { rest.trim().to_string() }
}

/// The passage's first sentence, at most `n` characters: what a door shows of it.
pub fn lead(text: &str, n: usize) -> String {
    let flat: String = text.split_whitespace().collect::<Vec<_>>().join(" ");
    let end = flat
        .char_indices()
        .find(|&(i, c)| matches!(c, '.' | '!' | '?') && flat[i + 1..].starts_with(' ') && i > 20)
        .map(|(i, _)| i + 1)
        .unwrap_or(flat.len());
    flat[..end].chars().take(n).collect()
}

/// A commit trailer (`Co-Authored-By: ...`, `Signed-off-by: ...`): who, not what, so not part of a passage.
fn is_trailer(line: &str) -> bool {
    let l = line.trim_start().to_lowercase();
    ["co-authored-by:", "signed-off-by:", "reviewed-by:", "change-id:", "\u{1f916} generated with"].iter().any(|t| l.starts_with(t))
}

fn git(repo: &Path, args: &[&str]) -> Result<String> {
    let out = Command::new("git").arg("-C").arg(repo).args(args).output()?;
    if !out.status.success() {
        return Err(format!("git {}: {}", args.join(" "), String::from_utf8_lossy(&out.stderr)).into());
    }
    Ok(String::from_utf8_lossy(&out.stdout).into_owned())
}

/// Cut a file into passages: markdown by heading, then by paragraph up to `CHUNK`; code and other text by blank-line
/// blocks up to `CHUNK`. Byte ranges are into the file as read.
fn cut(rel: &str, text: &str) -> Vec<(String, usize, usize)> {
    let md = rel.ends_with(".md") || rel.ends_with(".markdown");
    let mut out: Vec<(String, usize, usize)> = vec![];
    let mut heading = String::new();
    let (mut start, mut pos) = (0usize, 0usize);
    let mut start_heading = String::new();
    let close = |out: &mut Vec<(String, usize, usize)>, h: &str, a: usize, b: usize| {
        if text[a..b].trim().len() >= 20 {
            out.push((h.to_string(), a, b));
        }
    };
    for line in text.split_inclusive('\n') {
        let end = pos + line.len();
        let is_heading = md && line.starts_with('#');
        let blank = line.trim().is_empty();
        if is_heading && pos > start {
            close(&mut out, &start_heading, start, pos);
            start = pos;
        }
        if is_heading {
            heading = line.trim_start_matches('#').trim().to_string();
            start_heading = heading.clone();
        }
        if blank && end - start >= CHUNK {
            close(&mut out, &start_heading, start, end);
            start = end;
            start_heading = heading.clone();
        } else if end - start >= 2 * CHUNK {
            close(&mut out, &start_heading, start, end);
            start = end;
            start_heading = heading.clone();
        }
        pos = end;
    }
    if pos > start {
        close(&mut out, &start_heading, start, pos);
    }
    out
}

fn wanted(path: &Path) -> bool {
    let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("").to_lowercase();
    let name = path.file_name().and_then(|n| n.to_str()).unwrap_or("");
    (TEXT_EXT.contains(&ext.as_str()) || CODE_EXT.contains(&ext.as_str()) || ["README", "LICENSE", "Makefile", "Dockerfile"].contains(&name))
        && !name.ends_with(".lock")
        && std::fs::metadata(path).map(|m| m.len() <= MAX_FILE).unwrap_or(false)
}

fn files(root: &Path, is_git: bool) -> Result<Vec<String>> {
    if is_git {
        let mut v: Vec<String> = git(root, &["ls-files"])?.lines().map(String::from).filter(|f| wanted(&root.join(f))).collect();
        v.sort();
        return Ok(v);
    }
    let mut out = vec![];
    let mut stack = vec![PathBuf::new()];
    while let Some(rel) = stack.pop() {
        let mut entries: Vec<_> = std::fs::read_dir(root.join(&rel))?.filter_map(|e| e.ok()).collect();
        entries.sort_by_key(|e| e.file_name());
        for e in entries {
            let name = e.file_name().to_string_lossy().into_owned();
            let r = rel.join(&name);
            if e.path().is_dir() {
                if !name.starts_with('.') && !SKIP_DIRS.contains(&name.as_str()) {
                    stack.push(r);
                }
            } else if wanted(&e.path()) {
                out.push(r.to_string_lossy().into_owned());
            }
        }
    }
    out.sort();
    Ok(out)
}

/// The passages of a folder or git repository (its tracked files at the working tree, and its commit messages), or of
/// a JSON-lines file of `{id, title, text}`. `at` is the source path as configured, which pointers carry.
pub fn passages(root: &Path, at: &str) -> Result<Vec<Passage>> {
    let mut out = vec![];
    if root.is_file() {
        for (n, line) in std::fs::read_to_string(root)?.lines().enumerate() {
            if line.trim().is_empty() {
                continue;
            }
            let v: serde_json::Value = serde_json::from_str(line).map_err(|e| format!("{}:{}: {e}", root.display(), n + 1))?;
            let id = v["id"].as_str().ok_or_else(|| format!("{}:{}: no id", root.display(), n + 1))?.to_string();
            out.push(Passage {
                title: v["title"].as_str().unwrap_or("").to_string(),
                text: v["text"].as_str().unwrap_or("").to_string(),
                pointer: format!("jsonl:{at}#{}", n + 1),
                after: None,
                at: None,
                id,
            });
        }
        return Ok(out);
    }
    let is_git = root.join(".git").exists();
    for rel in files(root, is_git)? {
        let Ok(text) = std::fs::read_to_string(root.join(&rel)) else { continue };
        let mut prev: Option<String> = None;
        for (i, (heading, a, b)) in cut(&rel, &text).into_iter().enumerate() {
            let id = format!("{rel}#{}", i + 1);
            let title = if heading.is_empty() { rel.clone() } else { format!("{rel} › {heading}") };
            out.push(Passage { id: id.clone(), title, text: text[a..b].to_string(), pointer: format!("doc:{at}#{a}-{b}"), after: prev.clone(), at: None });
            prev = Some(id);
        }
    }
    if is_git {
        let log = git(root, &["log", "HEAD", "--format=%x1e%H%x1f%P%x1f%at%x1f%s%x1f%b"])?;
        for rec in log.split('\x1e').filter(|r| !r.trim().is_empty()) {
            let f: Vec<&str> = rec.splitn(5, '\x1f').collect();
            if f.len() < 5 {
                continue;
            }
            let (sha, parents, t, subject, body) = (f[0].trim(), f[1], f[2].parse::<i64>().ok(), f[3], f[4]);
            out.push(Passage {
                id: format!("commit/{}", &sha[..10]),
                title: format!("commit {}: {}", &sha[..7], subject),
                text: format!("{subject}\n\n{}", body.lines().filter(|l| !is_trailer(l)).collect::<Vec<_>>().join("\n").trim()),
                pointer: format!("git:{at}@{sha}"),
                after: parents.split_whitespace().next().map(|p| format!("commit/{}", &p[..10])),
                at: t,
            });
        }
    }
    Ok(out)
}

/// The facts for a set of passages: the graph the walk reads, and the D6 door's data.
pub fn facts(ps: &[Passage], graph: &str) -> Result<Vec<FactIn>> {
    let held: Vec<BTreeSet<String>> = ps.iter().map(|p| terms(&format!("{}\n{}", p.title, p.text))).collect();
    let mut df: HashMap<&str, usize> = HashMap::new();
    for ts in &held {
        for t in ts {
            *df.entry(t.as_str()).or_default() += 1;
        }
    }
    let ids: BTreeSet<&str> = ps.iter().map(|p| p.id.as_str()).collect();
    let mut facts = vec![];
    let with = |f: FactIn, at: Option<i64>| if let Some(t) = at { f.at(t) } else { f };
    // a name held by more than one passage in twenty (and more than five) is the corpus's vocabulary, not a name
    // that tells passages apart (`is_empty`, `serde_json`), so no door lists it
    let named: Vec<Vec<String>> = ps.iter().map(|p| names(&p.text)).collect();
    let mut name_df: HashMap<&str, usize> = HashMap::new();
    for ns in &named {
        for n in ns {
            *name_df.entry(n.as_str()).or_default() += 1;
        }
    }
    let common = (ps.len() / 20).max(5);
    for (i, (p, ts)) in ps.iter().zip(&held).enumerate() {
        let me = item(&p.id);
        if lit(&p.pointer) != format!("lit:{}", p.pointer) {
            return Err(format!("{}: the pointer {:?} is too long to store; use a shorter source path", p.id, p.pointer).into());
        }
        facts.push(with(FactIn::new(&me, Pred::Label, lit(if p.title.is_empty() { &p.id } else { &p.title }), graph), p.at));
        facts.push(with(FactIn::new(&me, Pred::Pointer, lit(&p.pointer), graph), p.at));
        for t in ts.iter().filter(|t| (2..=TERM_MAX_DF).contains(&df[t.as_str()]) && lit(t) == format!("lit:{t}")) {
            facts.push(with(FactIn::new(&me, Pred::Tagged, format!("lit:{t}"), graph), p.at));
        }
        for n in named[i].iter().filter(|n| name_df[n.as_str()] <= common).take(40) {
            facts.push(with(FactIn::new(&me, Pred::Named, lit(n), graph), p.at));
        }
    }
    // beside: both ways along each file or history
    let mut beside: BTreeMap<&str, BTreeSet<&str>> = BTreeMap::new();
    for p in ps {
        if let Some(a) = p.after.as_deref().filter(|a| ids.contains(a)) {
            beside.entry(p.id.as_str()).or_default().insert(a);
            beside.entry(a).or_default().insert(p.id.as_str());
        }
    }
    for (d, xs) in &beside {
        for x in xs {
            facts.push(FactIn::new(item(d), Pred::Beside, item(x), graph));
        }
    }
    // near: tf-idf cosine over unigram content words, candidates through terms held by at most NEAR_DF passages
    let n = ps.len() as f64;
    let vecs: Vec<HashMap<String, f64>> = ps
        .iter()
        .map(|p| {
            let mut tf: HashMap<String, f64> = HashMap::new();
            for w in words(&format!("{}\n{}", p.title, p.text)) {
                *tf.entry(w).or_default() += 1.0;
            }
            let mut v: HashMap<String, f64> = HashMap::new();
            for (w, f) in tf {
                if let Some(&d) = df.get(w.as_str()) {
                    if d >= 2 {
                        v.insert(w, (1.0 + f.ln()) * (n / d as f64).ln());
                    }
                }
            }
            let norm = v.values().map(|x| x * x).sum::<f64>().sqrt();
            if norm > 0.0 {
                v.values_mut().for_each(|x| *x /= norm);
            }
            v
        })
        .collect();
    let mut post: HashMap<&str, Vec<usize>> = HashMap::new();
    for (i, v) in vecs.iter().enumerate() {
        for w in v.keys() {
            if df[w.as_str()] <= NEAR_DF {
                post.entry(w.as_str()).or_default().push(i);
            }
        }
    }
    for (i, v) in vecs.iter().enumerate() {
        let mut score: HashMap<usize, f64> = HashMap::new();
        for (w, x) in v {
            for &j in post.get(w.as_str()).into_iter().flatten() {
                if j != i {
                    *score.entry(j).or_default() += x * vecs[j][w];
                }
            }
        }
        let mut best: Vec<(usize, f64)> = score.into_iter().filter(|&(_, s)| s >= NEAR_MIN).collect();
        best.sort_by(|a, b| b.1.total_cmp(&a.1).then(ps[a.0].id.cmp(&ps[b.0].id)));
        for (j, _) in best.into_iter().take(NEAR) {
            facts.push(FactIn::new(item(&ps[i].id), Pred::Near, item(&ps[j].id), graph));
        }
    }
    Ok(facts)
}

/// The graph one documents source writes: its facts are kept apart, so a re-ingest compares with its own only.
pub fn graph_of(at: &str) -> String {
    format!("documents:{at}")
}

/// The adapter: passages, then their facts, less what the store already holds for this source. A re-ingest of
/// unchanged files writes nothing; a changed file's old facts are retracted and its new ones asserted, so a walk at
/// the new head never sees a term or link the files no longer have (and one pinned to an older transaction still
/// does).
pub fn documents(root: &Path, at: &str, store: &Store, t: u32) -> Result<Ingested> {
    let ps = passages(root, at)?;
    if ps.is_empty() {
        return Err(format!("{}: no passages found (text, markdown or code files, or a .jsonl of {{id, title, text}})", root.display()).into());
    }
    let graph = graph_of(at);
    let new = facts(&ps, &graph)?;
    let held: HashSet<(String, String, String)> =
        store.graph_facts(t, &graph, store.head(t)?)?.into_iter().map(|(s, p, o)| (s, p.name().to_string(), o)).collect();
    let wanted: HashSet<(String, String, String)> = new.iter().map(|f| (f.s.clone(), f.p.clone(), f.o.clone())).collect();
    let mut out: Vec<FactIn> = new.into_iter().filter(|f| !held.contains(&(f.s.clone(), f.p.clone(), f.o.clone()))).collect();
    let mut gone: Vec<&(String, String, String)> = held.iter().filter(|k| !wanted.contains(*k)).collect();
    gone.sort();
    for (s, p, o) in gone {
        let pred = Pred::from_name(p).ok_or_else(|| format!("{p}: not a predicate"))?;
        let mut f = FactIn::new(s, pred, o, &graph);
        f.retract = true;
        out.push(f);
    }
    Ok(Ingested { facts: out, read: (ps.len(), "passages") })
}

/// A passage's text, read back through its pointer. `dir` is the folder holding avalanche.toml, against which a
/// source path is resolved. Files are read once per reader.
#[derive(Default)]
pub struct Reader {
    dir: PathBuf,
    files: HashMap<PathBuf, String>,
    lines: HashMap<PathBuf, Vec<String>>,
    /// repository → commit → message, read in one `git log` the first time a commit is asked for
    commits: HashMap<PathBuf, HashMap<String, String>>,
}

impl Reader {
    pub fn new(dir: &Path) -> Reader {
        Reader { dir: dir.to_path_buf(), ..Reader::default() }
    }

    /// The text of passage `doc` (its id, as `item:` names it without the prefix), through its pointer. A file
    /// passage's pointer holds its source and byte range, and its id the file's path within the source
    /// (`notes/a.md#2`), because a stored value is cut at 120 characters and a path can be longer.
    pub fn text(&mut self, doc: &str, pointer: &str) -> Result<String> {
        if let Some(rest) = pointer.strip_prefix("doc:") {
            let (root, range) = rest.rsplit_once('#').ok_or_else(|| format!("{pointer}: no byte range"))?;
            let (a, b) = range.split_once('-').ok_or_else(|| format!("{pointer}: bad byte range"))?;
            let (a, b): (usize, usize) = (a.parse()?, b.parse()?);
            let (rel, _) = doc.rsplit_once('#').ok_or_else(|| format!("{doc}: a file passage's id is path#n"))?;
            let p = self.dir.join(root).join(rel);
            if !self.files.contains_key(&p) {
                let t = std::fs::read_to_string(&p).map_err(|e| format!("{}: {e}", p.display()))?;
                self.files.insert(p.clone(), t);
            }
            let t = &self.files[&p];
            return Ok(t.get(a..b.min(t.len())).ok_or_else(|| format!("{pointer}: the file changed since ingestion"))?.to_string());
        }
        if let Some(rest) = pointer.strip_prefix("jsonl:") {
            let (path, n) = rest.rsplit_once('#').ok_or_else(|| format!("{pointer}: no line"))?;
            let n: usize = n.parse()?;
            let p = self.dir.join(path);
            if !self.lines.contains_key(&p) {
                let t = std::fs::read_to_string(&p).map_err(|e| format!("{}: {e}", p.display()))?;
                self.lines.insert(p.clone(), t.lines().map(String::from).collect());
            }
            let line = self.lines[&p].get(n - 1).ok_or_else(|| format!("{pointer}: no such line"))?;
            let v: serde_json::Value = serde_json::from_str(line)?;
            return Ok(v["text"].as_str().unwrap_or("").to_string());
        }
        if let Some(rest) = pointer.strip_prefix("git:") {
            let (path, sha) = rest.rsplit_once('@').ok_or_else(|| format!("{pointer}: no commit"))?;
            let repo = self.dir.join(path);
            if !self.commits.contains_key(&repo) {
                // one process for the whole history: a git show per commit took four minutes on 18,509 commits
                let log = git(&repo, &["log", "--all", "--format=%x1e%H%x1f%B"])?;
                let m = log.split('\x1e').filter_map(|r| r.split_once('\x1f')).map(|(h, b)| (h.trim().to_string(), b.to_string())).collect();
                self.commits.insert(repo.clone(), m);
            }
            if let Some(b) = self.commits[&repo].get(sha) {
                return Ok(b.clone());
            }
            return git(&repo, &["show", "-s", "--format=%B", sha]);
        }
        Err(format!("{pointer}: not a pointer this reader knows").into())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn terms_keep_content_words_and_adjacent_pairs() {
        let t = terms("The invoice total is rounded half-even. Banker's rounding");
        assert!(t.contains("invoice") && t.contains("invoice total") && t.contains("banker"));
        assert!(!t.contains("the") && !t.contains("total rounded"), "{t:?}");
    }

    #[test]
    fn names_skip_the_sentence_opener() {
        let n = names("Rounding happens in round_total. Then Banker's rounding, per ADR Seven, is applied by InvoiceWriter.");
        assert!(n.contains(&"round_total".to_string()) && n.contains(&"InvoiceWriter".to_string()), "{n:?}");
        assert!(n.iter().any(|x| x.starts_with("ADR")), "{n:?}");
        assert!(!n.contains(&"Rounding".to_string()) && !n.contains(&"Then".to_string()), "{n:?}");
    }

    #[test]
    fn markdown_cuts_at_headings_and_ranges_read_back() {
        let text = "# Title\n\nAn opening paragraph long enough to keep.\n\n## Part two\n\nThe second part says something else entirely.\n";
        let cuts = cut("a.md", text);
        assert_eq!(cuts.len(), 2);
        assert_eq!(cuts[1].0, "Part two");
        assert!(text[cuts[1].1..cuts[1].2].contains("second part"));
    }

    #[test]
    fn lead_is_the_first_sentence() {
        assert_eq!(lead("Avalanche is a database of a kind.  It has no SQL.", 200), "Avalanche is a database of a kind.");
        assert_eq!(lead("short", 3), "sho");
    }
}
