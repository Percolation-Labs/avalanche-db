pub fn export(rows: &[(String, i64)], cur: &str) -> String { rows.iter().map(|(k, v)| format!("{k},{cur}{v}\n")).collect() }
