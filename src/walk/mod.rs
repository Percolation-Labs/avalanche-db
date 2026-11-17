//! WALK: pure algorithm over the store. Search draws the circle, a session steps through
//! the frontier of open questions, and why prints the result. Nothing here calls a model, except `jev`: the
//! decider that ranks a wave's doors with the decision model, behind the Decider trait.

pub mod agent;
pub mod describe;
pub mod explore;
pub mod jev;
pub mod mcp;
pub mod p8ql;
pub mod search;
pub mod session;
pub mod suite;
pub mod text;
pub mod d6;
pub mod doors;
pub mod kappa;
pub mod lab;
pub mod world;
