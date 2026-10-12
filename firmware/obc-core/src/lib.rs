//! Open Bed Climate core: hardware-independent control, safety supervisor and wire protocols.
//!
//! `no_std`, no allocation, no clocks: every function takes `now` explicitly, so the same
//! code runs on the Pico 2 and in host tests. The Python package `software/obc` is the
//! reference; `tests/golden.rs` replays traces generated from it.
#![cfg_attr(not(test), no_std)]

pub mod control;
pub mod driver;
pub mod modbus;
pub mod ntc;
pub mod protocol;
