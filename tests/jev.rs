//! The walk an agent calls (specs/doors.md, `walk::agent`): Jev asked exactly as the lab asks it, answers replayed
//! with no network, `midb walk` with no key, and the MCP tools over stdio.
mod common;

use std::collections::BTreeMap;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use avalanche::config::Config;
use avalanche::infer::{body_key, Model};
use avalanche::walk::describe::{self, Doc, Docs};
use avalanche::walk::doors::{by_score, Attrs, Batch, Decider};
use avalanche::walk::jev::{self, JevDecider};
use avalanche::walk::lab::Clue;
use serde_json::{json, Value};

fn fixture() -> Value {
    serde_json::from_str(include_str!("fixtures/jev-requests.json")).unwrap()
}

fn tmp(name: &str) -> PathBuf {
    let d = std::env::temp_dir().join(format!("midb-jev-{name}-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&d);
    std::fs::create_dir_all(&d).unwrap();
    d
}

struct Page {
    question: String,
    found: Option<Vec<String>>,
    doors: BTreeMap<String, Clue>,
    attrs: BTreeMap<String, Attrs>,
    texts: BTreeMap<String, String>,
    bodies: Vec<String>,
}

/// A fixture page, its door texts built here by `describe::lines` from the page's documents.
fn page(p: &Value) -> Page {
    let docs: Docs = p["docs"].as_object().unwrap().iter().map(|(k, v)| (k.clone(), serde_json::from_value::<Doc>(v.clone()).unwrap())).collect();
    let mut doors = BTreeMap::new();
    let mut attrs = BTreeMap::new();
    let mut texts = BTreeMap::new();
    for c in p["clues"].as_array().unwrap() {
        let c = Clue {
            key: c["key"].as_str().unwrap().into(),
            kind: c["kind"].as_str().unwrap().into(),
            x: c["x"].as_str().unwrap().into(),
            source: c["source"].as_str().unwrap().into(),
            targets: serde_json::from_value(c["targets"].clone()).unwrap(),
            wave: 1,
            p: None,
        };
        let post = p["post"][&c.x].as_u64().unwrap_or(0) as usize;
        let t = describe::lines(&c, &c.targets, &docs, post);
        attrs.insert(c.key.clone(), Attrs { kind: c.kind.clone(), immediate: vec![t.clone()], ..Attrs::default() });
        texts.insert(c.key.clone(), t);
        doors.insert(c.key.clone(), c);
    }
    Page {
        question: p["question"].as_str().unwrap().into(),
        found: serde_json::from_value(p["found"].clone()).unwrap(),
        doors,
        attrs,
        texts,
        bodies: serde_json::from_value(p["bodies"].clone()).unwrap(),
    }
}

fn model(dir: &Path) -> Model {
    Model::open(dir, &Config::discover(dir).unwrap()).unwrap()
}

/// Every door text and every request body is byte for byte what the lab's own Python builds for the same page
/// (tests/fixtures/jev_requests.py: describe.lines, jevcache.requests, Noul.wire and httpx's encoder).
#[test]
fn requests_are_byte_identical_to_the_labs() {
    let fx = fixture();
    assert_eq!(fx["task"], jev::TASK_LINES);
    let dir = tmp("parity");
    let mut m = model(&dir);
    assert_eq!(m.name(), fx["model"].as_str().unwrap(), "the default model is the one the lab pins");
    let mut checked = 0;
    for p in fx["pages"].as_array().unwrap() {
        let pg = page(p);
        let want: BTreeMap<String, String> = serde_json::from_value(p["texts"].clone()).unwrap();
        for (k, t) in &want {
            assert_eq!(&pg.texts[k], t, "{}: door {k}'s text differs from describe.lines", p["name"]);
        }
        let mut d = JevDecider::new(&mut m);
        assert_eq!(d.keys, jev::Keys::F2, "F2 is the default");
        let b = Batch { question: &pg.question, wave: 1, doors: &pg.doors, attrs: &pg.attrs, reads: &[], label_version: "describe-lines/1".into() };
        let f2: Vec<String> = serde_json::from_value(p["f2_bodies"].clone()).unwrap();
        for (keys, want) in [(jev::Keys::C, &pg.bodies), (jev::Keys::F2, &f2)] {
            d.keys = keys;
            let got: Vec<String> = d.bodies(&b, pg.found.as_deref()).into_iter().map(|(_, b)| b).collect();
            assert_eq!(got.len(), want.len(), "{}: a different cut", p["name"]);
            for (i, (g, w)) in got.iter().zip(want).enumerate() {
                assert_eq!(g, w, "{} {keys:?}: request {i} differs from the lab's bytes", p["name"]);
                checked += 1;
            }
        }
    }
    assert!(checked >= 34, "only {checked} requests compared");
    assert!(fx["pages"].as_array().unwrap().iter().any(|p| p["name"] == "round3" && p["found"].as_array().is_some_and(|f| f.len() > 100)), "no request carries kappa's found");
    let _ = std::fs::remove_dir_all(&dir);
}

/// F2 over D6 doors: each option's key is the lab's `present("F2")` of the door's head line, its text the D6 text,
/// byte for byte as the lab's presenter and client write them.
#[test]
fn d6_doors_carry_the_labs_f2_keys() {
    let fx = fixture();
    let p = &fx["d6"];
    let texts: BTreeMap<String, String> = serde_json::from_value(p["texts"].clone()).unwrap();
    let mut doors = BTreeMap::new();
    let mut attrs = BTreeMap::new();
    for (k, t) in &texts {
        doors.insert(k.clone(), Clue { key: k.clone(), kind: k.split(':').next().unwrap().into(), x: String::new(), source: String::new(), targets: vec![], wave: 1, p: None });
        attrs.insert(k.clone(), Attrs { immediate: t.split('\n').map(String::from).collect(), ..Attrs::default() });
    }
    let dir = tmp("d6f2");
    let mut m = model(&dir);
    let d = JevDecider::new(&mut m);
    let q = p["question"].as_str().unwrap();
    let b = Batch { question: q, wave: 1, doors: &doors, attrs: &attrs, reads: &[], label_version: "d6/1".into() };
    let want: Vec<String> = serde_json::from_value(p["f2_bodies"].clone()).unwrap();
    let got: Vec<String> = d.bodies(&b, None).into_iter().map(|(_, b)| b).collect();
    assert!(want.len() >= 3, "the page is cut into several requests");
    assert_eq!(got, want);
    let _ = std::fs::remove_dir_all(&dir);
}

/// The cut alone, where it is most fragile: cumulative bytes one short of, on and one past 24,000, the 60-option
/// cut, and keys whose collation is not byte order. Each case's groups are jevcache.requests' own.
#[test]
fn requests_cut_where_the_labs_cut() {
    let fx = fixture();
    let cases = fx["cuts"].as_array().unwrap();
    assert_eq!(cases.len(), 6);
    for c in cases {
        let texts: BTreeMap<String, String> = serde_json::from_value(c["texts"].clone()).unwrap();
        let want: Vec<Vec<String>> = serde_json::from_value(c["requests"].clone()).unwrap();
        assert_eq!(jev::requests(&texts), want);
    }
}

/// With a kappa hook, the reads before a wave become `found` in every request's state, after the question and task;
/// an empty past adds nothing, as the lab's `if f:`.
#[test]
fn kappa_goes_in_the_state_as_found() {
    let fx = fixture();
    let pg = page(&fx["pages"][1]);
    let dir = tmp("kappa");
    let mut m = model(&dir);
    let mut d = JevDecider::new(&mut m);
    d.kappa = Some(Box::new(|reads: &[avalanche::walk::lab::Read]| Ok(reads.iter().map(|r| format!("{} said this.", r.doc)).collect())));
    let reads = vec![avalanche::walk::lab::Read { doc: "d001".into(), wave: 0, ord: 1, via: Some("search".into()) }];
    let b = Batch { question: &pg.question, wave: 1, doors: &pg.doors, attrs: &pg.attrs, reads: &reads, label_version: "describe-lines/1".into() };
    let f = d.found(&b).unwrap();
    assert_eq!(f.as_deref(), Some(&["d001 said this.".to_string()][..]));
    let body = &d.bodies(&b, f.as_deref())[0].1;
    assert!(body.contains(&format!("\"task\":{},\"found\":[\"d001 said this.\"]}},\"questions\"", serde_json::to_string(jev::TASK_LINES).unwrap())), "{body}");
    let empty = Batch { reads: &[], ..b };
    assert_eq!(d.found(&empty).unwrap(), None);
    let _ = std::fs::remove_dir_all(&dir);
}

/// kappa_state.relations (round 3's K6 and round 4's K7), ported: the same sentences, order and caps as the lab's.
#[test]
fn kappa_relations_are_the_labs() {
    let fx = fixture();
    let cases = fx["kappa"].as_array().unwrap();
    assert!(cases.iter().any(|c| c["found"].as_array().unwrap().iter().map(|s| s.as_str().unwrap().chars().count()).sum::<usize>() > 5900), "no case reaches the 6,000-character cap");
    for c in cases {
        let texts: Vec<String> = serde_json::from_value(c["texts"].clone()).unwrap();
        let via: Vec<Option<String>> = serde_json::from_value(c["via"].clone()).unwrap();
        let want: Vec<String> = serde_json::from_value(c["found"].clone()).unwrap();
        let got = jev::relations(&texts, &via, 200, 6000, c["recent_last"].as_bool().unwrap(), c["door_first"].as_bool().unwrap());
        assert_eq!(got, want, "{} reads, recent_last {}, door_first {}", texts.len(), c["recent_last"], c["door_first"]);
    }
}

/// A real MuSiQue page, answered from what Jev said to the lab's run (the lab's cache), recorded in decisions.jsonl:
/// the decider ranks it with no key and no network, merged by raw P, and says it sent nothing.
#[test]
fn a_recorded_page_replays_without_the_network() {
    let fx = fixture();
    let p = fx["pages"].as_array().unwrap().iter().find(|p| p.get("recorded").is_some()).expect("a page with recorded answers");
    let pg = page(p);
    let rec: Vec<Vec<f64>> = serde_json::from_value(p["recorded"].clone()).unwrap();
    let dir = tmp("replay");
    std::fs::create_dir_all(dir.join(".avalanche")).unwrap();
    let mut f = std::fs::File::create(dir.join(".avalanche/decisions.jsonl")).unwrap();
    for (b, ps) in pg.bodies.iter().zip(&rec) {
        let answers: serde_json::Map<String, Value> = ps.iter().enumerate().map(|(j, p)| (format!("c{j}"), json!({"type": "noul", "noul": p}))).collect();
        let line = json!({"key": body_key(b), "request": serde_json::from_str::<Value>(b).unwrap(), "response": {"model": "jev-1.13.0", "answers": answers, "usage": {"input_tokens": 1000}}});
        writeln!(f, "{line}").unwrap();
    }
    drop(f);
    let mut m = model(&dir);
    assert!(m.recorded_all(&pg.bodies));
    let mut d = JevDecider::new(&mut m);
    d.keys = jev::Keys::C;
    let b = Batch { question: &pg.question, wave: 1, doors: &pg.doors, attrs: &pg.attrs, reads: &[], label_version: "describe-lines/1".into() };
    let ranking = d.rank(&b).unwrap();
    let mut want = vec![];
    for ((ks, _), ps) in d.bodies(&b, None).iter().zip(&rec) {
        want.extend(ks.iter().cloned().zip(ps.iter().copied()));
    }
    assert_eq!(ranking, by_score(want));
    assert_eq!(ranking.len(), pg.doors.len());
    let w = &d.waves[0];
    assert_eq!((w.requests, w.replayed, w.called, w.input_tokens), (rec.len(), rec.len(), 0, 0), "a replay sends and costs nothing");
    let _ = std::fs::remove_dir_all(&dir);
}

fn midb(dir: &Path, home: &Path, args: &[&str]) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_midb")).arg("-C").arg(dir).args(args).env_remove("AVALANCHE_MODEL_KEY").env("HOME", home).env("PATH", "/usr/bin:/bin").output().unwrap()
}

/// A tiny lab-imported conversation (the doors tests' synthetic graph) with a document text each.
fn lab_fixture(name: &str) -> (PathBuf, PathBuf, PathBuf) {
    let dir = tmp(name);
    std::fs::write(dir.join("graphs.jsonl"), common::graph_line() + "\n").unwrap();
    let store = dir.join("lab.redb");
    let out = midb(&dir, &dir, &["lab", "import", dir.join("graphs.jsonl").to_str().unwrap(), "--store", store.to_str().unwrap()]);
    assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr));
    let docs = dir.join("docs.jsonl");
    let mut f = std::fs::File::create(&docs).unwrap();
    for i in 0..common::DOCS {
        let d = common::doc(i);
        let topic = ["invoices", "rounding", "exports", "support"][i % 4];
        writeln!(f, "{}", json!({"uri": d, "title": format!("Note {i}"), "said": format!("Note {i} is about {topic} and the cent.")})).unwrap();
    }
    (dir, store, docs)
}

#[test]
fn midb_walk_with_no_key_ranks_doors_by_search_order_and_says_so() {
    let (dir, store, docs) = lab_fixture("nokey");
    let args = ["walk", "which notes are about rounding?", "--store", store.to_str().unwrap(), "--conv", common::CONV, "--docs", docs.to_str().unwrap(), "--reads", "80"];
    let out = midb(&dir, &dir, &[&args[..], &["--json"]].concat());
    assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr));
    let w: Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(w["decider"], "search-order");
    assert!(w["note"].as_str().unwrap().contains("no key"), "{}", w["note"]);
    let docs_out = w["documents"].as_array().unwrap();
    assert_eq!(docs_out.len(), 80);
    assert!(docs_out[..10].iter().all(|d| d["via"] == "search"), "the seeds are search's");
    assert!(docs_out.iter().any(|d| d["via"] != "search"), "the walk went through a door");
    assert!(docs_out[0]["location"].as_str().unwrap().starts_with("lab:"));
    assert_eq!(w["waves"].as_array().unwrap().len(), 2, "80 reads are two waves of 50");
    assert!(w["waves"].as_array().unwrap().iter().all(|x| x["opened"].as_array().unwrap().len() <= 1), "budget 1 opens one door a wave");
    assert_eq!(w["called"], 0);
    // the text form says the same, and read_document's reader reads the location back
    let text = String::from_utf8_lossy(&midb(&dir, &dir, &args).stdout).into_owned();
    assert!(text.starts_with("walk: 80 documents, 10 from search then one door a wave; decider search-order\nnote: no key"), "{text}");
    assert!(avalanche::walk::agent::content(&dir, docs_out[0]["id"].as_str().unwrap(), docs_out[0]["location"].as_str().unwrap()).unwrap().contains("the cent"));
    // search's order from a file holds the walk to it
    let order: Vec<String> = (0..common::DOCS).rev().map(common::doc).collect();
    std::fs::write(dir.join("order.json"), serde_json::to_string(&order).unwrap()).unwrap();
    let out = midb(&dir, &dir, &[&args[..], &["--json", "--order", dir.join("order.json").to_str().unwrap()]].concat());
    let w: Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(w["documents"][0]["id"], order[0]);
    let _ = std::fs::remove_dir_all(&dir);
}

/// The caller's budget is k documents: s from search, then the rest through doors, one door a wave, exactly k.
#[test]
fn a_walk_returns_k_documents_s_from_search_the_rest_through_doors() {
    let (dir, store, docs) = lab_fixture("k");
    let base = ["walk", "which notes are about rounding?", "--store", store.to_str().unwrap(), "--conv", common::CONV, "--docs", docs.to_str().unwrap(), "--json"];
    for (extra, k, s) in [(vec![], 10usize, 3usize), (vec!["--budget", "25", "--seeds", "5"], 25, 5), (vec!["--budget", "2"], 2, 2), (vec!["--budget", "1"], 1, 1)] {
        let out = midb(&dir, &dir, &[&base[..], &extra[..]].concat());
        assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr));
        let w: Value = serde_json::from_slice(&out.stdout).unwrap();
        let d = w["documents"].as_array().unwrap();
        assert_eq!((d.len(), w["budget"].as_u64().unwrap() as usize, w["seeds"].as_u64().unwrap() as usize), (k, k, s), "{extra:?}");
        assert!(d[..s].iter().all(|x| x["via"] == "search"), "{extra:?}: the first s are search's");
        assert!(d[s..].iter().all(|x| x["via"] != "search"), "{extra:?}: the rest came through doors");
        let waves = w["waves"].as_array().unwrap();
        assert!(waves.iter().all(|x| x["opened"].as_array().unwrap().len() == 1), "{extra:?}: one door a wave");
        let ids: std::collections::HashSet<&str> = d.iter().map(|x| x["id"].as_str().unwrap()).collect();
        assert_eq!(ids.len(), k, "no document twice");
    }
    let _ = std::fs::remove_dir_all(&dir);
}

fn mcp(dir: &Path, extra: &[&str], calls: &[Value]) -> Vec<Value> {
    let mut child = Command::new(env!("CARGO_BIN_EXE_midb")).arg("-C").arg(dir).arg("mcp").args(extra)
        .env_remove("AVALANCHE_MODEL_KEY").env("HOME", dir).stdin(Stdio::piped()).stdout(Stdio::piped()).spawn().unwrap();
    let mut stdin = child.stdin.take().unwrap();
    for (i, c) in calls.iter().enumerate() {
        let mut m = c.clone();
        m["jsonrpc"] = json!("2.0");
        m["id"] = json!(i + 1);
        writeln!(stdin, "{m}").unwrap();
    }
    drop(stdin);
    let out = child.wait_with_output().unwrap();
    String::from_utf8_lossy(&out.stdout).lines().map(|l| serde_json::from_str(l).unwrap()).collect()
}

fn call(name: &str, args: Value) -> Value {
    json!({"method": "tools/call", "params": {"name": name, "arguments": args}})
}

fn text(r: &Value) -> &str {
    assert!(r["result"]["isError"].is_null(), "{r}");
    r["result"]["content"][0]["text"].as_str().unwrap()
}

/// What an agent does with a fresh folder: list the tools, ingest the folder, walk, read what the walk returned.
#[test]
fn the_mcp_tools_ingest_walk_and_read_a_folder() {
    let dir = tmp("mcp");
    std::fs::create_dir_all(dir.join("notes")).unwrap();
    std::fs::write(dir.join("notes/rounding.md"), "# Rounding\n\nInvoices round every total half-even, as ADR-007 decided after BUG-12.\n\n## Why half-even\n\nRounding halves away from zero drifts a cent on long invoices, which RoundingPolicy avoids.\n").unwrap();
    std::fs::write(dir.join("notes/export.md"), "# Export\n\nThe spreadsheet export writes each invoice total with its currency symbol, through SheetWriter.\n").unwrap();
    std::fs::write(dir.join("notes/support.md"), "# Support\n\nA customer said their invoice total was a cent off from their own spreadsheet; RoundingPolicy explained it.\n").unwrap();
    let r = mcp(&dir, &[], &[
        json!({"method": "tools/list"}),
        call("walk", json!({"question": "why is the invoice a cent off?"})),
        call("ingest_repo", json!({})),
        call("walk", json!({"question": "why is the invoice a cent off?", "budget": 3})),
        call("walk", json!({"question": "why is the invoice a cent off?", "budget": 3, "json": true})),
    ]);
    let names: Vec<&str> = r[0]["result"]["tools"].as_array().unwrap().iter().map(|t| t["name"].as_str().unwrap()).collect();
    for n in ["ingest_repo", "walk", "read_document", "search", "ask", "step", "why", "p8ql_schema", "p8ql_explain", "p8ql_run"] {
        assert!(names.contains(&n), "{n} is not listed: {names:?}");
    }
    assert_eq!(r[1]["result"]["isError"], true, "a walk before ingestion is refused");
    assert!(r[1]["result"]["content"][0]["text"].as_str().unwrap().contains("ingest_repo"), "{}", r[1]);
    assert!(text(&r[2]).contains("added a documents source"), "{}", text(&r[2]));
    assert!(text(&r[2]).contains("passages"), "{}", text(&r[2]));
    let walk = text(&r[3]);
    assert!(walk.starts_with("walk: 3 documents, 3 from search then one door a wave; decider search-order"), "{walk}");
    let first = walk.lines().nth(2).unwrap().split_whitespace().nth(1).unwrap().to_string();
    let j: Value = serde_json::from_str(text(&r[4])).unwrap();
    assert_eq!(j["documents"][0]["id"], first.as_str());
    let r = mcp(&dir, &[], &[call("read_document", json!({"id": first})), call("read_document", json!({"id": "no-such#1"}))]);
    assert!(text(&r[0]).contains("cent"), "{}", text(&r[0]));
    assert_eq!(r[1]["result"]["isError"], true);
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn the_mcp_walk_serves_a_lab_conversation() {
    let (dir, store, docs) = lab_fixture("mcplab");
    let extra = ["--store", store.to_str().unwrap(), "--conv", common::CONV, "--docs", docs.to_str().unwrap()];
    let r = mcp(&dir, &extra, &[call("walk", json!({"question": "rounding", "budget": 12})), call("read_document", json!({"id": common::doc(3)}))]);
    assert!(text(&r[0]).starts_with("walk: 12 documents, 3 from search then one door a wave; decider search-order"), "{}", text(&r[0]));
    assert!(text(&r[1]).contains("Note 3 is about"), "{}", text(&r[1]));
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn mcp_install_prints_the_command_when_claude_is_not_here() {
    let dir = tmp("install");
    let out = midb(&dir, &dir, &["mcp", "install", "--scope", "project"]);
    assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr));
    let s = String::from_utf8_lossy(&out.stdout);
    let abs = std::fs::canonicalize(&dir).unwrap();
    assert!(s.starts_with("claude is not on PATH"), "{s}");
    assert!(s.contains(&format!("claude mcp add --scope project avalanche -- {} -C {} mcp", env!("CARGO_BIN_EXE_midb"), abs.display())), "{s}");
    assert!(s.contains("\"mcpServers\""), "{s}");
    assert!(!midb(&dir, &dir, &["mcp", "install", "--scope", "everywhere"]).status.success());
    let _ = std::fs::remove_dir_all(&dir);
}
