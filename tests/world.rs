use avalanche::construct::world;
use avalanche::store::Store;
use avalanche::walk::explore::{choose, Coin};
use avalanche::walk::world::World;

/// A world of six items in one sitting, written as reach.py writes one.
fn tiny(dir: &std::path::Path) {
    std::fs::create_dir_all(dir).unwrap();
    let ids = ["d0", "c1", "d2", "d3", "d4", "d5"];
    std::fs::write(dir.join("ids.json"), serde_json::to_string(&ids).unwrap()).unwrap();
    let mut facts = String::new();
    // d4 is tagged t0.e0.i after d0 and d2 were made, as an instruction question's tag is
    for (s, p, o) in [("d0", "tagged", "g0"), ("d0", "tagged", "t0.1"), ("d0", "in", "sitting:0"), ("c1", "tagged", "g0"), ("d0", "makes", "c1"),
        ("c1", "answers", "q:0.1"), ("d2", "tagged", "t0.1"), ("d2", "in", "sitting:0"), ("d3", "in", "sitting:0"), ("d4", "tagged", "t0.1"),
        ("d4", "in", "sitting:0"), ("d5", "in", "sitting:0"), ("d2", "tagged", "t0.e0.i"), ("d0", "tagged", "t0.e0.i")] {
        facts += &format!("{}\n", serde_json::json!([s, p, o]));
    }
    std::fs::write(dir.join("facts.jsonl"), facts).unwrap();
    // two dimensions: d0, d2 and d3 point one way, c1, d4 and d5 the other
    let v: [[f32; 2]; 6] = [[1.0, 0.0], [0.0, 1.0], [0.9, 0.1], [0.8, 0.3], [0.1, 0.9], [0.2, 0.8]];
    let header = "{'descr': '<f4', 'fortran_order': False, 'shape': (6, 2), }";
    let pad = 64 - (10 + header.len() + 1) % 64;
    let mut npy = b"\x93NUMPY\x01\x00".to_vec();
    npy.extend(((header.len() + pad + 1) as u16).to_le_bytes());
    npy.extend(header.as_bytes());
    npy.extend(std::iter::repeat_n(b' ', pad));
    npy.push(b'\n');
    npy.extend(v.iter().flatten().flat_map(|x| x.to_le_bytes()));
    std::fs::write(dir.join("vectors.npy"), npy).unwrap();
}

#[test]
fn a_world_answers_the_seven_questions_in_creation_order() {
    let dir = std::env::temp_dir().join(format!("ava-world-{}", std::process::id()));
    tiny(&dir);
    let store = Store::open(dir.join("avalanche.redb")).unwrap();
    let t = store.tenant("world").unwrap();
    let r = world::import(&store, t, &dir).unwrap();
    assert_eq!(r.items, 6);
    let w = World::open(&store, t).unwrap();
    let id = |n: &str| w.id(n).unwrap().unwrap();
    let names = |xs: Vec<u64>| xs.into_iter().map(|x| w.name(x).unwrap()).collect::<Vec<_>>();

    assert_eq!(names(w.tags_of(id("item:d0")).unwrap()), ["g0", "t0.1", "t0.e0.i"]);
    // in creation order, though d2 was tagged t0.e0.i before d0 was
    assert_eq!(names(w.tag_members(id("lit:t0.e0.i")).unwrap()), ["d0", "d2"]);
    assert_eq!(names(w.tag_members(id("lit:t0.1")).unwrap()), ["d0", "d2", "d4"]);
    assert_eq!(names(w.next(id("item:d3")).unwrap()), ["d0", "d2", "d4", "d5"], "two either side; c1 is in no sitting");
    assert_eq!(names(w.next(id("item:d0")).unwrap()), ["d2", "d3"]);
    assert_eq!(names(w.linked(id("item:c1")).unwrap()), ["d0", "0.1"]);
    assert_eq!(names(w.nearest(&[1.0, 0.0], 3)), ["d0", "d2", "d3"]);
    assert_eq!(w.vector(id("item:d4")).unwrap(), [0.1, 0.9]);
}

#[test]
fn nearest_meaning_is_each_items_three_nearest_both_ways() {
    let dir = std::env::temp_dir().join(format!("ava-world-near-{}", std::process::id()));
    tiny(&dir);
    let store = Store::open(dir.join("avalanche.redb")).unwrap();
    let t = store.tenant("world").unwrap();
    world::import(&store, t, &dir).unwrap();
    let w = World::open(&store, t).unwrap();
    let near = |n: &str| w.near(w.id(&format!("item:{n}")).unwrap().unwrap()).unwrap().into_iter().map(|x| w.name(x).unwrap()).collect::<Vec<_>>();
    // d0's three nearest are d2, d3 and d5; d2 and d3 name d0 among theirs, so nothing is added
    assert_eq!(near("d0"), ["d2", "d3", "d5"]);
    // c1's are d4, d5 and d3, listed in creation order
    assert_eq!(near("c1"), ["d3", "d4", "d5"]);
}

#[test]
fn the_coin_and_the_draw_match_the_reference() {
    // converge.py: Coin('walk:q1:333').random() three times
    let mut c = Coin::new("walk:q1:333");
    assert_eq!([c.next(), c.next(), c.next()], [0.4789502584370282, 0.43765145425451424, 0.6003145923108684]);
    assert_eq!(choose(&[0.2, 0.3, 0.5], 0.0), 0);
    assert_eq!(choose(&[0.2, 0.3, 0.5], 0.2), 1, "a running sum equal to the draw is not past it");
    assert_eq!(choose(&[0.2, 0.3, 0.5], 0.999), 2);
}
