//! Avalanche DB: a research engine for the Percolate pattern. Typed quads with valid and
//! transaction time in an append-only per-tenant log, indexed in four key orders on redb,
//! queried as iterative sessions whose every step lands in a usage graph.

//! Three layers over one store:
//! - construct: adapters and dreaming write facts (the data that must be built);
//! - infer: the decision model, recorded and replayable (the only place a model is called);
//! - walk: search, steps and why, pure algorithm over the store (never calls a model).

pub mod config;
pub mod construct;
pub mod infer;
pub mod model;
pub mod store;
pub mod walk;

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
