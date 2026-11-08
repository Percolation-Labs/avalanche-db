pub fn export(rows: &[(String, i64)], cur: &str) -> String { rows.iter().map(|(k, v)| format!("{k},{cur}{}.{:02}\n", v / 100, v % 100)).collect() }
