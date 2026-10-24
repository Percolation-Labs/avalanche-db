//! Avalanche DB: a research engine for the Percolate pattern. Typed quads with valid and
//! transaction time in an append-only per-tenant log, indexed in four key orders on redb,
//! queried as iterative sessions whose every step lands in a usage graph.

pub mod config;
pub mod dream;
pub mod ingest;
pub mod model;
pub mod search;
pub mod session;
pub mod store;

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
