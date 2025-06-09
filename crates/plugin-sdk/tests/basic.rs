use plugin_sdk::WasmPlugin;
use wasmtime::Engine;

#[test]
fn create_plugin() {
    let engine = Engine::default();
    let wasm: Vec<u8> = wasmtime::wat2wasm("(module)").unwrap();
    let plugin = WasmPlugin::new(&engine, &wasm).unwrap();
    let mut store = wasmtime::Store::new(&engine, ());
    let _instance = plugin.instantiate(&mut store).unwrap();
}
