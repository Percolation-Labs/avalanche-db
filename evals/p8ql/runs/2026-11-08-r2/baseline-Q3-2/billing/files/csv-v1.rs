pub fn export(rows: &[(String, i64)]) -> String { rows.iter().map(|(k, v)| format!("{k},{v}\n")).collect() }
