#![deny(clippy::all)]

use anyhow::Result;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::process::{Command};

pub struct PseudoTerminal {
    child: tokio::process::Child,
}

impl PseudoTerminal {
    pub async fn spawn(shell: &str) -> Result<Self> {
        let child = Command::new(shell)
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .spawn()?;
        Ok(Self { child })
    }

    pub async fn write(&mut self, bytes: &[u8]) -> Result<()> {
        if let Some(stdin) = &mut self.child.stdin {
            stdin.write_all(bytes).await?;
        }
        Ok(())
    }

    pub async fn read(&mut self) -> Result<Vec<u8>> {
        let mut buf = Vec::new();
        if let Some(stdout) = &mut self.child.stdout {
            stdout.read_to_end(&mut buf).await?;
        }
        Ok(buf)
    }
}
