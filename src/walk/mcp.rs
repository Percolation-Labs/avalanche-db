//! WALK, for an agent: the session API over MCP (JSON-RPC on stdin and stdout). An agent
//! gets the same four tools a person has, with the same text back: `search` draws the
//! circle, `ask` starts a walk and returns a token, `step` takes one step (steered with
//! `take` and `prefer`), and `why` runs a walk to its end. The store is opened for each
//! call and closed after it, so the CLI can use it between calls.

use std::io::{BufRead, Write};
use std::path::Path;

use serde_json::{json, Value};

use super::{p8ql, search};
use super::session::{self, Steer};
use crate::config::Config;
use crate::model::date;
use crate::store::Store;
use crate::Result;

const INSTRUCTIONS: &str = "Avalanche DB is a memory of this project's history that you walk, not search. \
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
        {"name": "p8ql_run", "description": "Run a P8QL statement: the plan, each step's rows and keys read, then the answer. A LIKE whose top candidates are close pauses and lists them; choose one with = '<name>' and run again.",
         "inputSchema": {"type": "object", "properties": {"statement": s("A P8QL statement")}, "required": ["statement"]}},
        {"name": "why", "description": "Run a walk to its end and return each record under the one that led to it, with dates and statistics.",
         "inputSchema": {"type": "object", "properties": {"question": s("The question, in words"),
            "valid_at": s("Walk only what was true on this date (YYYY-MM-DD)"), "prefer": prefer}, "required": ["question"]}}
    ])
}

fn call(dir: &Path, name: &str, a: &Value) -> Result<String> {
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

fn answer(dir: &Path, msg: &Value) -> Option<Value> {
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
            match call(dir, p["name"].as_str().unwrap_or_default(), &p["arguments"]) {
                Ok(text) => json!({"content": [{"type": "text", "text": text}]}),
                Err(e) => json!({"content": [{"type": "text", "text": e.to_string()}], "isError": true}),
            }
        }
        m => return Some(json!({"jsonrpc": "2.0", "id": id, "error": {"code": -32601, "message": format!("no method {m}")}})),
    };
    Some(json!({"jsonrpc": "2.0", "id": id, "result": result}))
}

/// Serve until stdin closes. Notifications get no reply.
pub fn serve(dir: &Path) -> Result<()> {
    let mut out = std::io::stdout().lock();
    for line in std::io::stdin().lock().lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        let reply = match serde_json::from_str::<Value>(&line) {
            Ok(msg) => answer(dir, &msg),
            Err(e) => Some(json!({"jsonrpc": "2.0", "id": null, "error": {"code": -32700, "message": e.to_string()}})),
        };
        if let Some(r) = reply {
            writeln!(out, "{r}")?;
            out.flush()?;
        }
    }
    Ok(())
}
