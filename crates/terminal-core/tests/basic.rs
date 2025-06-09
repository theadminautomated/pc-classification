use terminal_core::PseudoTerminal;

#[tokio::test]
async fn spawn_echo() {
    let mut pty = PseudoTerminal::spawn("/bin/echo").await.unwrap();
    pty.write(b"hello\n").await.unwrap();
    let out = pty.read().await.unwrap();
    assert!(out.starts_with(b"hello"));
}
