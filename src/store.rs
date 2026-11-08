//! One redb file per store. The truth is the per-tenant log; the four index orders are
//! written beside it in the same transaction. Every index key starts with the tenant and
//! ends with the transaction, so a graph step is one prefix range scan and an as-of-T
//! read is the same scan ignoring keys past T. Nothing is updated in place: a retraction
//! is another key.

use std::collections::BTreeMap;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

use redb::{Database, ReadableDatabase, ReadableTable, ReadableTableMetadata, TableDefinition};

use crate::model::{FactIn, Pred};
use crate::Result;

/// (tenant, a, b, c, d, tx) -> (op, valid_from, valid_to)
type Index = TableDefinition<'static, (u32, u64, u64, u64, u64, u64), (u8, i64, i64)>;

const SPOG: Index = TableDefinition::new("spog");
const OSPG: Index = TableDefinition::new("ospg");
const PSOG: Index = TableDefinition::new("psog");
const GSPO: Index = TableDefinition::new("gspo");
/// (tenant, tx, seq) -> (s, p, o, g, op, valid_from, valid_to)
const LOG: TableDefinition<(u32, u64, u32), (u64, u64, u64, u64, u8, i64, i64)> = TableDefinition::new("log");
/// (tenant, tx) -> (wall clock, facts written)
const TXS: TableDefinition<(u32, u64), (i64, u32)> = TableDefinition::new("txs");
const DICT: TableDefinition<(u32, &str), u64> = TableDefinition::new("dict");
const NAMES: TableDefinition<(u32, u64), &str> = TableDefinition::new("names");
const TENANTS: TableDefinition<&str, u32> = TableDefinition::new("tenants");
/// session id -> durable session state (JSON)
pub(crate) const SESSIONS: TableDefinition<&str, &str> = TableDefinition::new("sessions");
/// (tenant, node) -> its vector, little-endian f32. Written once per node by an import; not bitemporal.
const VECS: TableDefinition<(u32, u64), &[u8]> = TableDefinition::new("vecs");

const ASSERT: u8 = 1;
const RETRACT: u8 = 0;
/// Predicate ids are the enum's; interned names start above them.
const FIRST_NAME_ID: u64 = 1 << 16;

pub fn now() -> i64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs() as i64).unwrap_or(0)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Dir {
    Out,
    In,
}

/// One live edge as seen from the node a step started at.
#[derive(Clone, Debug)]
pub struct Edge {
    pub pred: Pred,
    pub dir: Dir,
    pub other: u64,
    pub graph: u64,
    pub tx: u64,
    pub valid_from: i64,
    pub valid_to: i64,
}

#[derive(Default, Clone, Copy, Debug)]
pub struct ScanCost {
    pub keys_read: u64,
}

pub struct Store {
    db: Database,
}

impl Store {
    pub fn open(path: impl AsRef<Path>) -> Result<Store> {
        let db = Database::create(path)?;
        let w = db.begin_write()?;
        for t in [SPOG, OSPG, PSOG, GSPO] {
            w.open_table(t)?;
        }
        w.open_table(LOG)?;
        w.open_table(TXS)?;
        w.open_table(DICT)?;
        w.open_table(NAMES)?;
        w.open_table(TENANTS)?;
        w.open_table(SESSIONS)?;
        w.open_table(VECS)?;
        w.commit()?;
        Ok(Store { db })
    }

    pub fn tenant(&self, name: &str) -> Result<u32> {
        if let Some(v) = self.db.begin_read()?.open_table(TENANTS)?.get(name)? {
            return Ok(v.value());
        }
        let w = self.db.begin_write()?;
        let id = {
            let mut t = w.open_table(TENANTS)?;
            let id = t.len()? as u32 + 1;
            t.insert(name, id)?;
            id
        };
        w.commit()?;
        Ok(id)
    }

    /// The tenant's usage log: a tenant of its own, `<name>#usage`, so walks have their own
    /// transactions and never move the data's T.
    pub fn usage_of(&self, tenant: u32) -> Result<u32> {
        let name = {
            let r = self.db.begin_read()?;
            let t = r.open_table(TENANTS)?;
            let mut found = None;
            for row in t.iter()? {
                let (k, v) = row?;
                if v.value() == tenant {
                    found = Some(k.value().to_string());
                }
            }
            found.ok_or_else(|| format!("no tenant {tenant}"))?
        };
        self.tenant(&format!("{name}#usage"))
    }

    /// The tenant's latest transaction, 0 before its first write.
    pub fn head(&self, tenant: u32) -> Result<u64> {
        let r = self.db.begin_read()?;
        let t = r.open_table(TXS)?;
        let last = t.range((tenant, 0)..=(tenant, u64::MAX))?.next_back().transpose()?;
        Ok(last.map(|(k, _)| k.value().1).unwrap_or(0))
    }

    /// Append one batch as one transaction. Every fact is checked against the type
    /// system first; one bad fact refuses the batch.
    pub fn write(&self, tenant: u32, facts: &[FactIn]) -> Result<u64> {
        let mut errors = vec![];
        let preds: Vec<Option<Pred>> = facts
            .iter()
            .map(|f| f.pred().map_err(|e| errors.push(format!("{} {} {}: {e}", f.s, f.p, f.o))).ok())
            .collect();
        if !errors.is_empty() {
            errors.truncate(10);
            return Err(format!("refused, nothing written:\n  {}", errors.join("\n  ")).into());
        }
        let wall = now();
        let w = self.db.begin_write()?;
        let tx = {
            let mut txs = w.open_table(TXS)?;
            let tx = txs.range((tenant, 0)..=(tenant, u64::MAX))?.next_back().transpose()?.map(|(k, _)| k.value().1).unwrap_or(0) + 1;
            txs.insert((tenant, tx), (wall, facts.len() as u32))?;
            tx
        };
        {
            let mut dict = w.open_table(DICT)?;
            let mut names = w.open_table(NAMES)?;
            let mut log = w.open_table(LOG)?;
            let mut idx = [w.open_table(SPOG)?, w.open_table(OSPG)?, w.open_table(PSOG)?, w.open_table(GSPO)?];
            let mut next = names.range((tenant, FIRST_NAME_ID)..=(tenant, u64::MAX))?.next_back().transpose()?.map(|(k, _)| k.value().1 + 1).unwrap_or(FIRST_NAME_ID);
            let mut intern = |name: &str| -> Result<u64> {
                if let Some(v) = dict.get((tenant, name))? {
                    return Ok(v.value());
                }
                let id = next;
                next += 1;
                dict.insert((tenant, name), id)?;
                names.insert((tenant, id), name)?;
                Ok(id)
            };
            for (seq, (f, p)) in facts.iter().zip(preds).enumerate() {
                let (s, p, o, g) = (intern(&f.s)?, p.unwrap().id(), intern(&f.o)?, intern(&format!("graph:{}", f.g))?);
                let op = if f.retract { RETRACT } else { ASSERT };
                let (vf, vt) = (f.valid_from.unwrap_or(wall), f.valid_to.unwrap_or(i64::MAX));
                log.insert((tenant, tx, seq as u32), (s, p, o, g, op, vf, vt))?;
                let v = (op, vf, vt);
                idx[0].insert((tenant, s, p, o, g, tx), v)?;
                idx[1].insert((tenant, o, s, p, g, tx), v)?;
                idx[2].insert((tenant, p, s, o, g, tx), v)?;
                idx[3].insert((tenant, g, s, p, o, tx), v)?;
            }
        }
        w.commit()?;
        Ok(tx)
    }

    pub fn id(&self, tenant: u32, name: &str) -> Result<Option<u64>> {
        Ok(self.db.begin_read()?.open_table(DICT)?.get((tenant, name))?.map(|v| v.value()))
    }

    /// Every interned name starting with `prefix` (`person:`), with its id: one range scan.
    pub fn names_with_prefix(&self, tenant: u32, prefix: &str) -> Result<Vec<(String, u64)>> {
        let r = self.db.begin_read()?;
        let t = r.open_table(DICT)?;
        let mut out = vec![];
        for row in t.range((tenant, prefix)..)? {
            let (k, v) = row?;
            let (tn, name) = k.value();
            if tn != tenant || !name.starts_with(prefix) {
                break;
            }
            out.push((name.to_string(), v.value()));
        }
        Ok(out)
    }

    pub fn graph_id(&self, tenant: u32, graph: &str) -> Result<Option<u64>> {
        self.id(tenant, &format!("graph:{graph}"))
    }

    pub fn name(&self, tenant: u32, id: u64) -> Result<String> {
        let r = self.db.begin_read()?;
        let t = r.open_table(NAMES)?;
        let v = t.get((tenant, id))?;
        Ok(v.map(|v| v.value().to_string()).unwrap_or_else(|| format!("#{id}")))
    }

    /// Every live edge at `node` in one direction as of transaction `as_of`, optionally only
    /// those valid at `valid_at`. One prefix scan: OUT reads SPOG, IN reads OSPG.
    pub fn edges(&self, tenant: u32, node: u64, dir: Dir, as_of: u64, valid_at: Option<i64>, cost: &mut ScanCost) -> Result<Vec<Edge>> {
        let r = self.db.begin_read()?;
        let t = r.open_table(if dir == Dir::Out { SPOG } else { OSPG })?;
        let (lo, hi) = ((tenant, node, 0, 0, 0, 0), (tenant, node, u64::MAX, u64::MAX, u64::MAX, u64::MAX));
        // Keys for one quad sort by tx, so the last one at or before as_of is its state.
        let mut latest: BTreeMap<(u64, u64, u64), (u64, u8, i64, i64)> = BTreeMap::new();
        for row in t.range(lo..=hi)? {
            let (k, v) = row?;
            cost.keys_read += 1;
            let (_, _, b, c, g, tx) = k.value();
            if tx > as_of {
                continue;
            }
            let (op, vf, vt) = v.value();
            latest.insert((b, c, g), (tx, op, vf, vt));
        }
        let mut out = vec![];
        for ((b, c, g), (tx, op, vf, vt)) in latest {
            if op != ASSERT || valid_at.is_some_and(|at| at < vf || at >= vt) {
                continue;
            }
            let (p, other) = if dir == Dir::Out { (b, c) } else { (c, b) };
            if let Some(pred) = Pred::from_id(p) {
                out.push(Edge { pred, dir, other, graph: g, tx, valid_from: vf, valid_to: vt });
            }
        }
        Ok(out)
    }

    /// Live (subject, object) pairs for one predicate, from PSOG.
    pub fn by_pred(&self, tenant: u32, pred: Pred, as_of: u64, cost: &mut ScanCost) -> Result<Vec<(u64, u64, u64)>> {
        let r = self.db.begin_read()?;
        let t = r.open_table(PSOG)?;
        let p = pred.id();
        let mut latest: BTreeMap<(u64, u64, u64), u8> = BTreeMap::new();
        for row in t.range((tenant, p, 0, 0, 0, 0)..=(tenant, p, u64::MAX, u64::MAX, u64::MAX, u64::MAX))? {
            let (k, v) = row?;
            cost.keys_read += 1;
            let (_, _, s, o, g, tx) = k.value();
            if tx <= as_of {
                latest.insert((s, o, g), v.value().0);
            }
        }
        Ok(latest.into_iter().filter(|(_, op)| *op == ASSERT).map(|(k, _)| k).collect())
    }

    /// Facts per graph as of `as_of`, from GSPO.
    pub fn graph_size(&self, tenant: u32, graph: u64, as_of: u64) -> Result<u64> {
        let r = self.db.begin_read()?;
        let t = r.open_table(GSPO)?;
        let mut latest: BTreeMap<(u64, u64, u64), u8> = BTreeMap::new();
        for row in t.range((tenant, graph, 0, 0, 0, 0)..=(tenant, graph, u64::MAX, u64::MAX, u64::MAX, u64::MAX))? {
            let (k, v) = row?;
            let (_, _, s, p, o, tx) = k.value();
            if tx <= as_of {
                latest.insert((s, p, o), v.value().0);
            }
        }
        Ok(latest.values().filter(|op| **op == ASSERT).count() as u64)
    }

    /// The tenant's transactions: (tx, wall clock, facts).
    pub fn transactions(&self, tenant: u32) -> Result<Vec<(u64, i64, u32)>> {
        let r = self.db.begin_read()?;
        let t = r.open_table(TXS)?;
        let mut out = vec![];
        for row in t.range((tenant, 0)..=(tenant, u64::MAX))? {
            let (k, v) = row?;
            let (wall, n) = v.value();
            out.push((k.value().1, wall, n));
        }
        Ok(out)
    }

    /// The facts one transaction appended, by name, in log order.
    pub fn log(&self, tenant: u32, tx: u64) -> Result<Vec<(String, Pred, String, String, bool)>> {
        let rows: Vec<_> = {
            let r = self.db.begin_read()?;
            let t = r.open_table(LOG)?;
            let mut rows = vec![];
            for row in t.range((tenant, tx, 0)..=(tenant, tx, u32::MAX))? {
                rows.push(row?.1.value());
            }
            rows
        };
        rows.into_iter()
            .map(|(s, p, o, g, op, _, _)| Ok((self.name(tenant, s)?, Pred::from_id(p).unwrap(), self.name(tenant, o)?, self.name(tenant, g)?, op == RETRACT)))
            .collect()
    }

    /// Store each named node's vector. Every name must already be interned.
    pub fn put_vectors(&self, tenant: u32, rows: &[(u64, Vec<f32>)]) -> Result<()> {
        let w = self.db.begin_write()?;
        {
            let mut t = w.open_table(VECS)?;
            for (id, v) in rows {
                let bytes: Vec<u8> = v.iter().flat_map(|x| x.to_le_bytes()).collect();
                t.insert((tenant, *id), bytes.as_slice())?;
            }
        }
        w.commit()?;
        Ok(())
    }

    /// Every vector the tenant holds, in node id order.
    pub fn vectors(&self, tenant: u32) -> Result<Vec<(u64, Vec<f32>)>> {
        let r = self.db.begin_read()?;
        let t = r.open_table(VECS)?;
        let mut out = vec![];
        for row in t.range((tenant, 0)..=(tenant, u64::MAX))? {
            let (k, v) = row?;
            out.push((k.value().1, v.value().chunks_exact(4).map(|b| f32::from_le_bytes([b[0], b[1], b[2], b[3]])).collect()));
        }
        Ok(out)
    }

    pub(crate) fn get_session(&self, id: &str) -> Result<Option<String>> {
        Ok(self.db.begin_read()?.open_table(SESSIONS)?.get(id)?.map(|v| v.value().to_string()))
    }

    pub(crate) fn put_session(&self, id: &str, json: &str) -> Result<()> {
        let w = self.db.begin_write()?;
        w.open_table(SESSIONS)?.insert(id, json)?;
        w.commit()?;
        Ok(())
    }
}
