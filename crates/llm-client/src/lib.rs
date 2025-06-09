#![deny(clippy::all)]

use anyhow::Result;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct CompletionRequest {
    pub prompt: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model: Option<String>,
}

#[derive(Serialize, Deserialize)]
pub struct CompletionResponse {
    pub content: String,
}

pub struct LlmClient {
    base_url: String,
    api_key: Option<String>,
}

impl LlmClient {
    pub fn new(base_url: impl Into<String>, api_key: Option<String>) -> Self {
        Self { base_url: base_url.into(), api_key }
    }

    pub async fn complete(&self, req: CompletionRequest) -> Result<CompletionResponse> {
        let client = reqwest::Client::new();
        let mut builder = client.post(format!("{}/v1/completions", self.base_url))
            .json(&req);
        if let Some(key) = &self.api_key {
            builder = builder.bearer_auth(key);
        }
        let resp = builder.send().await?.json::<CompletionResponse>().await?;
        Ok(resp)
    }
}
