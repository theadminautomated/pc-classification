#![deny(clippy::all)]

use anyhow::Result;
use wasmtime::{Engine, Module, Store, Instance};

pub struct WasmPlugin {
    module: Module,
}

impl WasmPlugin {
    pub fn new(engine: &Engine, wasm: &[u8]) -> Result<Self> {
        let module = Module::from_binary(engine, wasm)?;
        Ok(Self { module })
    }

    pub fn instantiate(&self, store: &mut Store<()>) -> Result<Instance> {
        let instance = Instance::new(store, &self.module, &[])?;
        Ok(instance)
    }
}
