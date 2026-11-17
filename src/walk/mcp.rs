//! WALK, for an agent: the session API over MCP (JSON-RPC on stdin and stdout). An agent
//! gets the same four tools a person has, with the same text back: `search` draws the
//! circle, `ask` starts a walk and returns a token, `step` takes one step (steered with
//! `take` and `prefer`), and `why` runs a walk to its end. The store is opened for each
//! call and closed after it, so the CLI can use it between calls.

use std::io::{BufRead, Write};
use std::path::Path;

use serde_json::{json, Value};

use super::agent::{self, Corpus};
use super::{p8ql, search};
use super::session::{self, Steer};
use crate::config::{Config, FILE};
use crate::construct::project;
use crate::model::date;
use crate::store::Store;
use crate::Result;

const INSTRUCTIONS: &str = "Avalanche DB is a memory of this project that you walk, not search. \
To find the documents a question needs: call ingest_repo once (it reads this folder's files and git history into the store), \
then walk with the question; it returns documents in reading order, each with its id, title, where it lives and how it was reached. \
Read the ones you need with read_document. \
For the project's typed history (commits, decisions, issues): \
Call ask with a question to start a walk; it returns a token. Call step with the token to take one step: \
it shows the record reached, the links it opened, the ranked open questions and the next token. \
Steer with take (an open question by name) or prefer (kind=weight, such as because=1,duplicates=0). \
why runs a whole walk and returns the tree; search shows what plain search finds. \
For a question with a known shape, such as who works with someone, write P8QL: p8ql_schema lists the kinds, \
links and named paths, p8ql_explain shows the plan before it runs, and p8ql_run runs it step by step.";

fn tools() -> Value {
    let s = |d: &str| json!({"type": "string", "description": d});
    let prefer = s("Change the priority policy: kind=weight, comma separated; 0 stops following a kind");
    json!([
        {"name": "ingest_repo", "description": "Read a folder of this project (its text, markdown and code files and its git history) into the store as passages, and build the doors a walk follows. Call it once before walk, and again after the files change. Creates the store if there is none. Returns what was read.",
         "inputSchema": {"type": "object", "properties": {"path": s("The folder to read, relative to the project (default \".\", the whole project)")}}},
        {"name": "walk", "description": "Find the documents a question needs. Search picks where to start; then each wave the decision model ranks the doors (leads to unread documents) and the walk opens the best. Returns documents in reading order: rank, id, how it was reached (search, or the door it came through) and its title, then where its content lives; then each wave's doors and what the ranking cost. Read a document with read_document.",
         "inputSchema": {"type": "object", "properties": {"question": s("The question, in words"),
            "budget": {"type": "integer", "description": "How many of a wave's top-ranked doors to open (default 1)"},
            "reads": {"type": "integer", "description": "How many documents to return (default 100)"},
            "kappa": {"type": "boolean", "description": "Give the ranking what the walk has read so far, one sentence a document (default true; false is the control)"},
            "json": {"type": "boolean", "description": "Return the walk as JSON instead of text (default false)"}}, "required": ["question"]}},
        {"name": "read_document", "description": "The content of one document walk returned, by its id: its title, where it lives, then its text.",
         "inputSchema": {"type": "object", "properties": {"id": s("A document id exactly as walk printed it")}, "required": ["id"]}},
        {"name": "search", "description": "Records whose labels share words with the question, best first: what plain search finds.",
         "inputSchema": {"type": "object", "properties": {"question": s("The question, in words")}, "required": ["question"]}},
        {"name": "ask", "description": "Start a walk at the record the question best matches. Returns a session token for step.",
         "inputSchema": {"type": "object", "properties": {"question": s("The question, in words, or a record name such as issue:BUG-12"),
            "valid_at": s("Walk only what was true on this date (YYYY-MM-DD)"), "prefer": prefer,
            "budget": {"type": "integer", "description": "How many records the walk may open (default 20)"}}, "required": ["question"]}},
        {"name": "step", "description": "Take one step of a walk: the best open question, or the one named by take. Returns what was reached, the ranked open questions, the step's statistics and the next token.",
         "inputSchema": {"type": "object", "properties": {"token": s("The token the last ask or step returned"),
            "take": s("An open question to take instead of the best one, by name"), "prefer": prefer}, "required": ["token"]}},
        {"name": "p8ql_schema", "description": "What a P8QL statement can name: the kinds of record with their counts, the link types with the kinds each joins, and the named paths.",
         "inputSchema": {"type": "object", "properties": {}}},
        {"name": "p8ql_explain", "description": "The plan for a P8QL statement, without running it: one line per step, the scan each uses and the transaction it is pinned to. A hop that cannot exist is refused here.",
         "inputSchema": {"type": "object", "properties": {"statement": s("A P8QL statement, such as SELECT colleague FROM person LIKE 'bob' AS b WALK b -[works_with]- person AS colleague")}, "required": ["statement"]}},
        {"name": "p8ql_run", "description": "Run a P8QL statement: the plan, each step's rows and keys read, then the answer. A LIKE on its own returns its nearest records with scores. Before WALK hops it carries the top one, or n with LIKE '…' WAVE n, and pauses on a near tie: choose one with = '<name>' and run again. For any question that follows reasons or a chain of work (why X, what led to X, what was done about the cause of X), one WALK FROM (SELECT r FROM record LIKE '…' AS r) FOLLOW because 1.0, implements 0.8 BUDGET 20 RETURN PATH prints the chain with its links and often answers alone. Links marked 'dreamed, not stated' were judged by a model, not stated by a source.",
         "inputSchema": {"type": "object", "properties": {"statement": s("A P8QL statement")}, "required": ["statement"]}},
        {"name": "why", "description": "Run a walk to its end and return each record under the one that led to it, with dates and statistics.",
         "inputSchema": {"type": "object", "properties": {"question": s("The question, in words"),
            "valid_at": s("Walk only what was true on this date (YYYY-MM-DD)"), "prefer": prefer}, "required": ["question"]}}
    ])
}

fn call(dir: &Path, corpus: &Corpus, name: &str, a: &Value) -> Result<String> {
    let num = |k: &str, d: usize| a[k].as_u64().map(|n| n as usize).unwrap_or(d);
    match name {
        "ingest_repo" => return ingest_repo(dir, a["path"].as_str().unwrap_or(".")),
        "walk" => {
            let q = a["question"].as_str().ok_or("walk needs question")?;
            let o = agent::Opts { budget: num("budget", 1), reads: num("reads", 100), order: None, kappa: a["kappa"].as_bool().unwrap_or(true) };
            let w = agent::walk(dir, corpus, q, &o)?;
            return Ok(if a["json"].as_bool().unwrap_or(false) { serde_json::to_string_pretty(&w)? } else { w.to_string() });
        }
        "read_document" => return agent::read_document(dir, corpus, a["id"].as_str().ok_or("read_document needs id")?),
        _ => {}
    }
    let cfg = Config::load(dir)?;
    let store = Store::open(Config::store_path(dir))?;
    let t = store.tenant(&cfg.tenant)?;
    let arg = |k: &str| a[k].as_str().map(String::from);
    let need = |k: &str| arg(k).ok_or_else(|| format!("{name} needs {k}"));
    let prefer: Vec<String> = arg("prefer").map(|p| p.split(',').map(String::from).collect()).unwrap_or_default();
    let prefer = session::parse_prefer(&prefer)?;
    let valid_at = arg("valid_at").map(|d| date::through(&d).ok_or(format!("{d}: not a date"))).transpose()?;
    let budget = a["budget"].as_u64().unwrap_or(20) as usize;
    Ok(match name {
        "search" => search::show(&search::search(&store, t, &need("question")?, store.head(t)?, None)?),
        "ask" => session::ask(&store, t, &need("question")?, budget, None, valid_at, &prefer)?.started(),
        "step" => session::step(&store, t, &need("token")?, &Steer { prefer, take: arg("take") })?.to_string(),
        "why" => session::why(&store, &session::walk(&store, t, &need("question")?, budget, None, valid_at, &prefer)?, None)?,
        "p8ql_schema" => p8ql::schema(&store, t, &cfg.paths)?,
        "p8ql_explain" => p8ql::explain(&store, t, &p8ql::parse(&need("statement")?, &cfg.paths)?)?.to_string(),
        "p8ql_run" => match p8ql::run(&store, t, &p8ql::parse(&need("statement")?, &cfg.paths)?)? {
            p8ql::Outcome::Done(s) | p8ql::Outcome::Paused(s) => s,
        },
        other => return Err(format!("no tool {other}").into()),
    })
}

fn answer(dir: &Path, corpus: &Corpus, msg: &Value) -> Option<Value> {
    let id = msg.get("id")?.clone();
    let result = match msg["method"].as_str().unwrap_or_default() {
        "initialize" => json!({
            "protocolVersion": msg["params"]["protocolVersion"].as_str().unwrap_or("2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "avalanche", "version": env!("CARGO_PKG_VERSION")},
            "instructions": INSTRUCTIONS,
        }),
        "ping" => json!({}),
        "tools/list" => json!({"tools": tools()}),
        "tools/call" => {
            let p = &msg["params"];
            match call(dir, corpus, p["name"].as_str().unwrap_or_default(), &p["arguments"]) {
                Ok(text) => json!({"content": [{"type": "text", "text": text}]}),
                Err(e) => json!({"content": [{"type": "text", "text": e.to_string()}], "isError": true}),
            }
        }
        m => return Some(json!({"jsonrpc": "2.0", "id": id, "error": {"code": -32601, "message": format!("no method {m}")}})),
    };
    Some(json!({"jsonrpc": "2.0", "id": id, "result": result}))
}

/// Serve until stdin closes. Notifications get no reply.
pub fn serve(dir: &Path, corpus: &Corpus) -> Result<()> {
    let mut out = std::io::stdout().lock();
    for line in std::io::stdin().lock().lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        let reply = match serde_json::from_str::<Value>(&line) {
            Ok(msg) => answer(dir, corpus, &msg),
            Err(e) => Some(json!({"jsonrpc": "2.0", "id": null, "error": {"code": -32700, "message": e.to_string()}})),
        };
        if let Some(r) = reply {
            writeln!(out, "{r}")?;
            out.flush()?;
        }
    }
    Ok(())
}

/// `ingest_repo`: the folder as a `documents` source (added to avalanche.toml when absent, after `midb init` when
/// there is no avalanche.toml), then `midb ingest` of that source.
pub fn ingest_repo(dir: &Path, path: &str) -> Result<String> {
    let mut out = String::new();
    if !dir.join(FILE).exists() {
        out += &project::init(dir)?;
    }
    let cfg = Config::load(dir)?;
    if !cfg.sources.iter().any(|s| s.adapter == "documents" && s.path == Path::new(path)) {
        let mut toml = std::fs::read_to_string(dir.join(FILE))?;
        toml += &format!("\n[[source]]\nadapter = \"documents\"\npath = {}\n", serde_json::to_string(path)?);
        std::fs::write(dir.join(FILE), toml)?;
        out += &format!("added a documents source, path {path:?}, to {FILE}\n");
    }
    // only that source: the folder's other sources keep their own `midb ingest`
    let cfg = Config::load(dir)?;
    let mut only = cfg.clone();
    only.sources.retain(|s| s.adapter == "documents" && s.path == Path::new(path));
    out += &project::ingest_with(dir, &only, &[], None)?;
    Ok(out)
}

fn on_path(bin: &str) -> Option<std::path::PathBuf> {
    std::env::var_os("PATH").and_then(|p| std::env::split_paths(&p).map(|d| d.join(bin)).find(|f| f.is_file()))
}

/// `midb mcp install`: register this store with Claude Code, or say exactly how.
pub fn install(dir: &Path, corpus: &Corpus, scope: &str) -> Result<String> {
    if !["local", "user", "project"].contains(&scope) {
        return Err(format!("scope is local, user or project, not {scope}").into());
    }
    let midb = std::env::current_exe()?;
    let dir = std::fs::canonicalize(dir)?;
    let mut args: Vec<String> = vec!["-C".into(), dir.display().to_string(), "mcp".into()];
    if let Corpus::Lab { store, conv, docs } = corpus {
        let abs = |p: &Path| std::fs::canonicalize(p).unwrap_or_else(|_| p.to_path_buf()).display().to_string();
        args.extend(["--store".into(), abs(store), "--conv".into(), conv.clone()]);
        if let Some(d) = docs {
            args.extend(["--docs".into(), abs(d)]);
        }
    }
    let mut cmd: Vec<String> = vec!["claude".into(), "mcp".into(), "add".into(), "--scope".into(), scope.into(), "avalanche".into(), "--".into(), midb.display().to_string()];
    cmd.extend(args.iter().cloned());
    let shown = cmd.iter().map(|a| if a.contains(' ') { format!("'{a}'") } else { a.clone() }).collect::<Vec<_>>().join(" ");
    if let Some(claude) = on_path("claude") {
        let out = std::process::Command::new(claude).args(&cmd[1..]).output()?;
        if !out.status.success() {
            return Err(format!("{shown}: {}{}", String::from_utf8_lossy(&out.stdout), String::from_utf8_lossy(&out.stderr)).into());
        }
        return Ok(format!("{shown}\n{}", String::from_utf8_lossy(&out.stdout)));
    }
    let config = json!({"mcpServers": {"avalanche": {"command": midb.display().to_string(), "args": args}}});
    Ok(format!("claude is not on PATH. Register the server with:\n  {shown}\nor add this to your MCP client's config:\n{}\n", serde_json::to_string_pretty(&config)?))
}
