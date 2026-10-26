//! CONSTRUCT: a synthetic reachability world (p8-subsystems REM-1191, reach.py `build`) read
//! into a tenant, so the engine can be measured on worlds whose every path to the evidence
//! is known. A world directory holds `ids.json` (items in the order they were made),
//! `facts.jsonl` (`[s, p, o]`), `vectors.npy` (one f32 row per id) and `questions.jsonl`.
//!
//! Items are written in `ids.json` order first, so a node's id is its creation order and
//! a prefix scan returns items in that order. Nearest meaning is computed here, once, from
//! the vectors: each item's three nearest by cosine, ties to the earlier item.

use std::path::Path;

use crate::model::FactIn;
use crate::store::Store;
use crate::Result;

/// How many nearest-meaning neighbours each item keeps (reach.py `NEAR`).
pub const NEAR: usize = 3;
const GRAPH: &str = "world";

pub struct Imported {
    pub items: usize,
    pub facts: usize,
    pub tx: u64,
}

/// A `.npy` file of little-endian f32 rows: (rows, columns, data).
pub fn read_npy(path: &Path) -> Result<(usize, usize, Vec<f32>)> {
    let b = std::fs::read(path)?;
    if b.len() < 10 || &b[..6] != b"\x93NUMPY" {
        return Err(format!("{}: not a .npy file", path.display()).into());
    }
    let (hlen, start) = if b[6] == 1 { (u16::from_le_bytes([b[8], b[9]]) as usize, 10) } else { (u32::from_le_bytes([b[8], b[9], b[10], b[11]]) as usize, 12) };
    let header = std::str::from_utf8(&b[start..start + hlen])?;
    if !header.contains("'<f4'") || header.contains("'fortran_order': True") {
        return Err(format!("{}: want C-ordered little-endian f32, got {header}", path.display()).into());
    }
    let shape = header.split("'shape': (").nth(1).and_then(|s| s.split(')').next()).ok_or("no shape")?;
    let dims: Vec<usize> = shape.split(',').filter_map(|x| x.trim().parse().ok()).collect();
    let (rows, cols) = match dims[..] {
        [r, c] => (r, c),
        _ => return Err(format!("{}: want two dimensions, got {shape}", path.display()).into()),
    };
    let data: Vec<f32> = b[start + hlen..].chunks_exact(4).map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
    if data.len() != rows * cols {
        return Err(format!("{}: {} values for shape ({rows}, {cols})", path.display(), data.len()).into());
    }
    Ok((rows, cols, data))
}

/// Similarity in f64: a product of two f32 is exact there, so engines differ only in the
/// order they sum, far below any gap between two items.
pub fn dot(a: &[f32], b: &[f32]) -> f64 {
    a.iter().zip(b).map(|(x, y)| *x as f64 * *y as f64).sum()
}

/// The item's node name: `d12` is `item:d12`.
pub fn item(id: &str) -> String {
    format!("item:{id}")
}

pub fn import(store: &Store, tenant: u32, dir: &Path) -> Result<Imported> {
    let ids: Vec<String> = serde_json::from_str(&std::fs::read_to_string(dir.join("ids.json"))?)?;
    let (rows, cols, data) = read_npy(&dir.join("vectors.npy"))?;
    if rows != ids.len() {
        return Err(format!("{} ids and {rows} vectors", ids.len()).into());
    }
    let mut facts: Vec<FactIn> = ids.iter().map(|i| FactIn::new(item(i), crate::model::Pred::Label, format!("lit:{i}"), GRAPH)).collect();
    for line in std::fs::read_to_string(dir.join("facts.jsonl"))?.lines().filter(|l| !l.is_empty()) {
        let [s, p, o]: [String; 3] = serde_json::from_str(line)?;
        let (p, o) = match p.as_str() {
            "is" => continue,
            "tagged" => ("tagged", format!("lit:{o}")),
            "in" => ("inSitting", format!("lit:{o}")),
            "makes" => ("makes", item(&o)),
            "answers" => ("answers", format!("question:{}", o.trim_start_matches("q:"))),
            _ => return Err(format!("{line}: no such world predicate").into()),
        };
        facts.push(FactIn { s: item(&s), p: p.into(), o, g: GRAPH.into(), valid_from: None, valid_to: None, retract: false });
    }
    let mut n = facts.len();
    store.write(tenant, &facts)?;

    let node: Vec<u64> = ids.iter().map(|i| store.id(tenant, &item(i)).map(|x| x.unwrap())).collect::<Result<_>>()?;
    let vecs: Vec<&[f32]> = data.chunks_exact(cols).collect();
    store.put_vectors(tenant, &node.iter().zip(&vecs).map(|(n, v)| (*n, v.to_vec())).collect::<Vec<_>>())?;

    let mut near = vec![];
    for (a, va) in vecs.iter().enumerate() {
        let mut best: Vec<(f64, usize)> = Vec::with_capacity(NEAR + 1);
        for (b, vb) in vecs.iter().enumerate() {
            if a == b {
                continue;
            }
            let s = dot(va, vb);
            if best.len() < NEAR || s > best[NEAR - 1].0 {
                let at = best.iter().position(|(x, _)| s > *x).unwrap_or(best.len());
                best.insert(at, (s, b));
                best.truncate(NEAR);
            }
        }
        for (_, b) in best {
            near.push(FactIn::new(item(&ids[a]), crate::model::Pred::Near, item(&ids[b]), GRAPH));
        }
    }
    n += near.len();
    let tx = store.write(tenant, &near)?;
    Ok(Imported { items: ids.len(), facts: n, tx })
}
