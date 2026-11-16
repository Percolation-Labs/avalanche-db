//! specs/doors.md: the lab walk on a Decider and a DoorLabeller, the budget as the caller's, and the batch log.
mod common;

use std::collections::{BTreeSet, HashSet};

use avalanche::walk::doors::{self, AttrFilter, Decider, GraphStats, KindOnly, Oracle, Random, Scores, SearchOrder};
use avalanche::walk::explore::Coin;
use avalanche::walk::lab::{self, Settings};

fn settings(v: serde_json::Value) -> Settings {
    serde_json::from_value(v).unwrap()
}

fn fixed() -> Scores<impl FnMut(&str) -> Option<f64>> {
    Scores("fixed".into(), |k: &str| Some(common::p_of(k)))
}

/// The golden file was captured from the engine before this refactor (the Decide closure and the .5 gate), with the
/// same graph, search orders and P. `Scores` gated at .5 must reproduce every walk read for read.
#[test]
fn the_gate_as_a_filter_reproduces_the_pre_refactor_walks() {
    let golden: serde_json::Value = serde_json::from_str(include_str!("fixtures/doors-golden.json")).unwrap();
    let (s, _dir) = common::store("parity");
    let cases = common::cases();
    assert_eq!(cases.len(), 12);
    for (name, q, st) in cases {
        let mut g = lab::Graph::open(&s, common::CONV).unwrap();
        let w = lab::run(&mut g, common::order(q), settings(st), "", &mut fixed(), &mut GraphStats).unwrap();
        let v = serde_json::to_value(&w).unwrap();
        let want = &golden[&name];
        for part in ["reads", "travelled", "clues", "log", "stop"] {
            assert_eq!(v[part], want[part], "{name}: {part} differs from the pre-refactor engine");
        }
        assert!(!w.travelled.is_empty(), "{name}: the walk opened no door, so parity would prove nothing");
    }
}

fn gold() -> HashSet<String> {
    // the documents search puts last for question 0: a walk only finds them through doors
    common::order(0).into_iter().rev().take(15).collect()
}

fn walk(d: &mut dyn Decider, l: &mut dyn doors::DoorLabeller, extra: serde_json::Value) -> lab::Walk {
    static N: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
    let (s, _dir) = common::store(&format!("w{}", N.fetch_add(1, std::sync::atomic::Ordering::SeqCst)));
    let mut st = serde_json::json!({"waves": 6, "wave": 20, "seeds": 5, "per_wave": 5, "cap": 30});
    st.as_object_mut().unwrap().extend(extra.as_object().unwrap().clone());
    let mut g = lab::Graph::open(&s, common::CONV).unwrap();
    lab::run(&mut g, common::order(0), settings(st), "which documents?", d, l).unwrap()
}

#[test]
fn every_wave_logs_its_whole_batch() {
    let w = walk(&mut fixed(), &mut GraphStats, serde_json::json!({}));
    assert_eq!(w.batches.len(), w.log.len());
    for b in &w.batches {
        assert_eq!(b.label_version, "graph-stats/1");
        assert_eq!(b.ranking.len(), b.doors.len(), "fixed scores judge every door, so the ranking is the whole batch");
        for d in &b.doors {
            assert!(d["attrs"]["stats"]["targets"].as_f64().unwrap() >= 1.0);
        }
        assert!(b.opened.iter().all(|k| w.travelled.contains_key(k)));
    }
    let opened: usize = w.batches.iter().map(|b| b.opened.len()).sum();
    assert_eq!(opened, w.travelled.len(), "every travelled door is logged as opened in exactly one wave");
}

#[test]
fn a_recorded_batch_rescores_another_decider_without_walking() {
    let gold = gold();
    let w = walk(&mut fixed(), &mut GraphStats, serde_json::json!({}));
    let mut oracle = Oracle(gold.clone());
    let mut random = Random(Coin::new("doors"));
    let (mut o_mrr, mut r_mrr, mut n) = (0.0, 0.0, 0);
    for ((wave, _, ro), (_, _, rr)) in doors::rescore(&w, "", &mut oracle).unwrap().into_iter().zip(doors::rescore(&w, "", &mut random).unwrap()) {
        let b = w.batches.iter().find(|b| b.wave == wave).unwrap();
        let rel = doors::relevant(b, &gold);
        assert_eq!(ro.len(), b.doors.len());
        if rel.is_empty() {
            continue;
        }
        let keys = |r: &[doors::Ranked]| r.iter().map(|x| x.key.clone()).collect::<Vec<_>>();
        let mo = doors::rank_metrics(&keys(&ro), &rel, 5);
        let mr = doors::rank_metrics(&keys(&rr), &rel, 5);
        assert_eq!(mo.mrr, 1.0, "the oracle puts a gold door first on every batch that has one");
        o_mrr += mo.mrr;
        r_mrr += mr.mrr;
        n += 1;
    }
    assert!(n > 0, "no recorded batch had a gold door; the test would prove nothing");
    assert!(o_mrr > r_mrr, "oracle {o_mrr} vs random {r_mrr} over {n} batches");
}

#[test]
fn rank_metrics_by_hand() {
    let rel: HashSet<String> = ["b", "d"].iter().map(|s| s.to_string()).collect();
    let r: Vec<String> = ["a", "b", "c", "d"].iter().map(|s| s.to_string()).collect();
    let m = doors::rank_metrics(&r, &rel, 3);
    assert_eq!(m.mrr, 0.5);
    assert_eq!(m.recall, 0.5);
    let ideal = 1.0 + 1.0 / 3f64.log2();
    assert!((m.ndcg - (1.0 / 3f64.log2()) / ideal).abs() < 1e-12);
}

#[test]
fn the_budget_caps_doors_per_wave() {
    let w = walk(&mut fixed(), &mut GraphStats, serde_json::json!({"open": 2}));
    assert!(w.batches.iter().all(|b| b.opened.len() <= 2));
    assert!(w.batches.iter().any(|b| b.opened.len() == 2));
    let free = walk(&mut fixed(), &mut GraphStats, serde_json::json!({}));
    assert!(free.travelled.len() > w.travelled.len());
    assert_eq!(w.reads.len(), free.reads.len(), "the reads budget is the same; only the doors cap moved");
}

#[test]
fn rank_order_opens_in_the_deciders_order() {
    // with no gate and order rank, the first door opened in wave 1 is the decider's top door
    let gold = gold();
    let w = walk(&mut Oracle(gold), &mut GraphStats, serde_json::json!({"order": "rank"}));
    let b1 = &w.batches[0];
    assert_eq!(b1.opened.first(), b1.ranking.first().map(|r| &r.key));
}

#[test]
fn filter_then_rank_keeps_only_what_the_filter_kept() {
    let mut d = AttrFilter { stat: "targets".into(), max: 3.0, inner: SearchOrder::new(&common::order(0)) };
    let w = walk(&mut d, &mut GraphStats, serde_json::json!({}));
    let mut opened_any = false;
    for b in &w.batches {
        let kept: BTreeSet<&str> = b.kept.as_ref().expect("the filter pass ran").iter().map(String::as_str).collect();
        for k in &b.opened {
            opened_any = true;
            let door = w.batches.iter().flat_map(|x| &x.doors).find(|d| d["key"] == k.as_str()).unwrap();
            assert!(door["attrs"]["stats"]["targets"].as_f64().unwrap() <= 3.0, "{k} was opened but has too many targets");
            assert!(kept.contains(k.as_str()) || w.batches.iter().any(|x| x.kept.as_ref().unwrap().contains(k)), "{k} opened without being kept");
        }
    }
    assert!(opened_any);
    // the same filter on a labeller that gives no statistics keeps nothing, so nothing opens
    let mut d = AttrFilter { stat: "targets".into(), max: 3.0, inner: SearchOrder::new(&common::order(0)) };
    let w = walk(&mut d, &mut KindOnly, serde_json::json!({}));
    assert!(w.travelled.is_empty());
}

#[test]
fn search_order_ranks_by_the_targets_best_search_place() {
    let order = common::order(0);
    let w = walk(&mut SearchOrder::new(&order), &mut GraphStats, serde_json::json!({"order": "rank"}));
    let pos: std::collections::HashMap<&str, usize> = order.iter().enumerate().map(|(i, d)| (d.as_str(), i)).collect();
    for b in &w.batches {
        let best: Vec<usize> = b.ranking.iter().map(|r| {
            let d = b.doors.iter().find(|d| d["key"] == r.key.as_str()).unwrap();
            d["targets"].as_array().unwrap().iter().map(|t| pos[t.as_str().unwrap()]).min().unwrap()
        }).collect();
        assert!(best.windows(2).all(|w| w[0] <= w[1]), "wave {}: ranking is not in search order", b.wave);
    }
}

#[test]
fn a_door_label_does_not_depend_on_the_question() {
    let (s, _dir) = common::store("noq");
    let run = |q: &str| {
        let mut g = lab::Graph::open(&s, common::CONV).unwrap();
        lab::run(&mut g, common::order(1), settings(serde_json::json!({"waves": 3, "wave": 20, "seeds": 5, "cap": 30})), q, &mut fixed(), &mut GraphStats).unwrap()
    };
    let (a, b) = (run("who wrote it?"), run("something else entirely"));
    for (x, y) in a.batches.iter().zip(&b.batches) {
        assert_eq!(x.doors, y.doors);
    }
}

#[test]
fn the_door_module_never_calls_the_model() {
    assert!(!include_str!("../src/walk/doors.rs").contains("infer"));
    assert!(!include_str!("../src/walk/lab.rs").contains("infer"));
}

/// specs/doors.md, read order: `per_door` caps the reads one opened door spends, and `within` orders them from the
/// graph alone. The default (`graph`, no cap) is today's walk, which the golden test above holds.
#[test]
fn per_door_caps_the_reads_one_door_spends() {
    for m in [1usize, 2] {
        let w = walk(&mut fixed(), &mut GraphStats, serde_json::json!({"per_door": m}));
        assert!(!w.travelled.is_empty());
        let mut by_door: std::collections::HashMap<&str, usize> = std::collections::HashMap::new();
        for r in &w.reads {
            if let Some(v) = r.via.as_deref().filter(|v| *v != "search") {
                *by_door.entry(v).or_default() += 1;
            }
        }
        assert!(by_door.values().all(|&n| n <= m), "per_door {m}: a door read more than {m} targets");
        let all = walk(&mut fixed(), &mut GraphStats, serde_json::json!({}));
        assert!(w.travelled.len() > all.travelled.len(), "per_door {m}: the reads a door gives up go to further doors");
    }
}

#[test]
fn within_postings_reads_the_same_door_in_another_order() {
    let a = walk(&mut fixed(), &mut GraphStats, serde_json::json!({"per_door": 1}));
    let b = walk(&mut fixed(), &mut GraphStats, serde_json::json!({"per_door": 1, "within": "postings"}));
    assert_ne!(
        a.reads.iter().map(|r| &r.doc).collect::<Vec<_>>(),
        b.reads.iter().map(|r| &r.doc).collect::<Vec<_>>(),
        "with one read per door, choosing it by postings must change which target is read"
    );
    let bad = std::panic::catch_unwind(|| walk(&mut fixed(), &mut GraphStats, serde_json::json!({"within": "question"})));
    assert!(bad.is_err(), "an unknown within (such as one built from the question) is refused");
}

/// specs/doors.md, the third pass: under `within: decider` the decider orders an opened door's unread targets and
/// may use the question; `per_door` then reads the top of that order. Default off, so today's walk is unchanged.
#[test]
fn within_decider_reads_the_targets_the_decider_puts_first() {
    let gold = gold();
    let place: std::collections::HashMap<String, usize> = gold.iter().map(|d| (d.clone(), 0)).collect();
    let mut td = doors::TargetOrder { inner: fixed(), place };
    let w = walk(&mut td, &mut GraphStats, serde_json::json!({"per_door": 1, "within": "decider"}));
    let logged: Vec<&doors::TargetLog> = w.batches.iter().flat_map(|b| b.targets.iter()).collect();
    assert!(!logged.is_empty(), "every opened door's target order is logged");
    for t in &logged {
        let first_gold = t.order.iter().position(|d| gold.contains(d));
        if let Some(i) = first_gold {
            assert_eq!(i, 0, "a door holding gold puts it first under the target oracle");
        }
    }
    let base = walk(&mut fixed(), &mut GraphStats, serde_json::json!({"per_door": 1}));
    let hit = |w: &lab::Walk| w.reads.iter().filter(|r| r.via.as_deref() != Some("search") && gold.contains(&r.doc)).count();
    assert!(hit(&w) >= hit(&base), "reading the gold target first never reads less gold through doors");
}

#[test]
fn within_decider_without_a_third_pass_is_the_graph_order() {
    let a = walk(&mut fixed(), &mut GraphStats, serde_json::json!({"per_door": 1}));
    let b = walk(&mut fixed(), &mut GraphStats, serde_json::json!({"per_door": 1, "within": "decider"}));
    assert_eq!(a.reads.iter().map(|r| &r.doc).collect::<Vec<_>>(), b.reads.iter().map(|r| &r.doc).collect::<Vec<_>>());
    assert!(b.batches.iter().all(|b| b.targets.is_empty()), "nothing is logged when the decider has no third pass");
}
