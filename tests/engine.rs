use avalanche::model::{FactIn, Pred};
use avalanche::walk::session::{self, Steer};

fn mentions() -> Vec<(String, f64)> {
    vec![("mentions".into(), 0.4)]
}
use avalanche::store::{Dir, ScanCost, Store};

fn store(name: &str) -> Store {
    let path = std::env::temp_dir().join(format!("ava-test-{name}-{}.redb", std::process::id()));
    let _ = std::fs::remove_file(&path);
    Store::open(path).unwrap()
}

fn seed(s: &Store, t: u32) -> u64 {
    s.write(t, &[
        FactIn::new("question:q1", Pred::Label, "lit:should memory be placed by the user", "claims"),
        FactIn::new("claim:c1", Pred::Answers, "question:q1", "claims"),
        FactIn::new("claim:c1", Pred::Label, "lit:people find things where they put them", "claims"),
        FactIn::new("claim:c1", Pred::Informs, "card:REM-1", "extracted"),
        FactIn::new("commit:aaaaaaaaaa", Pred::Mentions, "card:REM-1", "repo"),
    ])
    .unwrap()
}

fn out(s: &Store, t: u32, node: &str, as_of: u64) -> Vec<String> {
    let id = s.id(t, node).unwrap().unwrap();
    s.edges(t, id, Dir::Out, as_of, None, &mut ScanCost::default()).unwrap().iter().map(|e| format!("{} {}", e.pred.name(), s.name(t, e.other).unwrap())).collect()
}

#[test]
fn a_fact_outside_the_type_system_refuses_the_batch() {
    let s = store("types");
    let t = s.tenant("a").unwrap();
    let err = s.write(t, &[
        FactIn::new("claim:c1", Pred::Answers, "question:q1", "claims"),
        FactIn::new("claim:c1", Pred::Fixes, "issue:BUG-1", "claims"),
    ]);
    assert!(err.unwrap_err().to_string().contains("fixes cannot start at claim:c1"));
    assert_eq!(s.head(t).unwrap(), 0, "nothing written");
    let bad = FactIn { p: "relatesTo".into(), ..FactIn::new("claim:c1", Pred::Label, "lit:x", "claims") };
    assert!(s.write(t, &[bad]).is_err());
}

#[test]
fn a_retraction_is_a_fact_and_as_of_sees_before_it() {
    let s = store("asof");
    let t = s.tenant("a").unwrap();
    let t1 = seed(&s, t);
    let t2 = s.write(t, &[FactIn { retract: true, ..FactIn::new("claim:c1", Pred::Informs, "card:REM-1", "extracted") }]).unwrap();
    assert!(out(&s, t, "claim:c1", t1).contains(&"informs card:REM-1".to_string()));
    assert!(!out(&s, t, "claim:c1", t2).contains(&"informs card:REM-1".to_string()));
    assert_eq!(s.log(t, t2).unwrap().len(), 1, "the retraction is in the log");
}

#[test]
fn tenants_do_not_see_each_other() {
    let s = store("tenants");
    let (a, b) = (s.tenant("a").unwrap(), s.tenant("b").unwrap());
    seed(&s, a);
    assert!(s.id(b, "claim:c1").unwrap().is_none());
    assert_eq!(s.head(b).unwrap(), 0);
}

#[test]
fn a_session_walks_from_question_to_decision_and_logs_every_step() {
    let s = store("session");
    let t = s.tenant("a").unwrap();
    seed(&s, t);
    let sess = session::ask(&s, t, "placed by the user", 10, None, None, &mentions()).unwrap();
    assert_eq!(sess.start, "question:q1");
    let mut token = sess.token();
    let mut seen = vec![];
    for _ in 0..4 {
        let step = session::step(&s, t, &token, &Steer::default()).unwrap();
        seen.push(step.at.as_ref().unwrap().node.clone());
        assert!(step.stats.keys_read > 0);
        match step.token {
            Some(tk) => token = tk,
            None => break,
        }
    }
    assert_eq!(seen, ["question:q1", "claim:c1", "card:REM-1", "commit:aaaaaaaaaa"]);
    // The old token is stale once the session has moved on.
    assert!(session::step(&s, t, &sess.token(), &Steer::default()).err().unwrap().to_string().contains("stale token"));
    let u = s.usage_of(t).unwrap();
    let visits = s.by_pred(u, Pred::Visited, s.head(u).unwrap(), &mut ScanCost::default()).unwrap();
    assert_eq!(visits.len(), 4);
}

#[test]
fn a_session_pinned_before_a_write_does_not_see_it() {
    let s = store("pinned");
    let t = s.tenant("a").unwrap();
    let t1 = seed(&s, t);
    let sess = session::ask(&s, t, "question:q1", 10, Some(t1), None, &[]).unwrap();
    s.write(t, &[FactIn::new("claim:c2", Pred::Answers, "question:q1", "claims")]).unwrap();
    let step = session::step(&s, t, &sess.token(), &Steer::default()).unwrap();
    assert!(step.neighbours.iter().all(|n| n.node != "claim:c2"));
}

#[test]
fn walking_never_moves_the_data_transaction() {
    let s = store("usagelog");
    let t = s.tenant("a").unwrap();
    let t1 = seed(&s, t);
    for _ in 0..3 {
        session::walk(&s, t, "question:q1", 10, None, None, &mentions()).unwrap();
    }
    assert_eq!(s.head(t).unwrap(), t1);
    assert!(s.head(s.usage_of(t).unwrap()).unwrap() >= 3);
}

#[test]
fn the_agent_steers_by_policy_and_by_name() {
    let s = store("steer");
    let t = s.tenant("a").unwrap();
    seed(&s, t);
    s.write(t, &[FactIn::new("claim:c2", Pred::Answers, "question:q1", "claims"), FactIn::new("claim:c2", Pred::Informs, "card:REM-2", "claims")]).unwrap();
    let sess = session::ask(&s, t, "question:q1", 10, None, None, &[]).unwrap();
    let first = session::step(&s, t, &sess.token(), &Steer::default()).unwrap();
    assert_eq!(first.session.frontier.len(), 2, "both claims are open");
    // Take the second-ranked claim by name, then stop following informs mid-walk.
    let other = first.session.ranked()[1].node.clone();
    let took = session::step(&s, t, &first.token.unwrap(), &Steer { take: Some(other.clone()), prefer: vec![("informs".into(), 0.0)] }).unwrap();
    assert_eq!(took.at.unwrap().node, other);
    assert!(took.neighbours.iter().all(|n| n.pred != Pred::Informs), "informs was turned off");
    let u = s.usage_of(t).unwrap();
    assert_eq!(s.by_pred(u, Pred::Took, s.head(u).unwrap(), &mut ScanCost::default()).unwrap().len(), 1);
}

#[test]
fn the_walk_layer_never_calls_the_model() {
    for src in [include_str!("../src/walk/session.rs"), include_str!("../src/walk/search.rs"), include_str!("../src/walk/suite.rs"), include_str!("../src/walk/mcp.rs"), include_str!("../src/walk/p8ql.rs")] {
        assert!(!src.contains("infer"), "walk/ must not reach the model");
    }
}
