//! KAPPA: the walk's past, as state a decider reads with the doors (p8-subsystems `meta/lab/worlds/kappa_state.py`,
//! `relations`; `results/kappa/RESULT.md`, round 3). K6 is the opening sentence of every read, the reads a door led
//! to first and the most recent first, each cut at 200 characters, all of them at 6,000. On MuSiQue it added +.046
//! [+.014, +.080] NDCG to Jev's door ranking on top of D6; the order is worth at most .01 (round 4), the sentences
//! are the gain. Like a door, it is built from ingested text and the walk's reads, never the question.
//!
//! A decider puts it in the request's state as `found` (a list of strings), next to `question` and `task`.

use super::lab::{Graph, Read};
use crate::construct::documents::{body, lead, Reader};
use crate::model::Pred;
use crate::Result;

pub const CAP_EACH: usize = 200;
pub const CAP_ALL: usize = 6000;

/// K6 from the walk's reads so far. `reads` in walk order; a read's `via` is `search` or the door it came through.
pub fn k6(reads: &[Read], g: &mut Graph, reader: &mut Reader) -> Result<Vec<String>> {
    let recent: Vec<&Read> = reads.iter().rev().collect();
    let by_door = |r: &&Read| r.via.as_deref().is_some_and(|v| !v.starts_with("search"));
    let ordered: Vec<&Read> = recent.iter().copied().filter(by_door).chain(recent.iter().copied().filter(|r| !by_door(r))).collect();
    let (mut out, mut used) = (vec![], 0);
    for r in ordered {
        let title = g.values(&r.doc, Pred::Label)?.into_iter().next().unwrap_or_default();
        let text = match g.values(&r.doc, Pred::Pointer)?.into_iter().next() {
            Some(p) => reader.text(&r.doc, &p)?,
            None => String::new(),
        };
        // the lab's sentence is the first of "title\n\ntext", so it carries the title: kept here as "title: sentence"
        let s: String = format!("{title}: {}", lead(&body(&title, &text), CAP_EACH)).chars().take(CAP_EACH).collect();
        if used + s.chars().count() > CAP_ALL {
            break;
        }
        used += s.chars().count();
        out.push(s);
    }
    Ok(out)
}
