// Halves go to even, once per invoice total; see the decision record.
pub fn round_total(x: f64) -> i64 { let r = x.round(); if (x - x.trunc()).abs() == 0.5 && r % 2.0 != 0.0 { (r - x.signum()) as i64 } else { r as i64 } }
