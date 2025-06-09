use llm_client::LlmClient;
use llm_client::CompletionRequest;

#[tokio::test]
async fn construct_client() {
    let client = LlmClient::new("http://localhost:11434", None);
    let req = CompletionRequest { prompt: "hello".into(), model: None };
    // We only check that the request building doesn't fail up to sending.
    let _ = client.complete(req).await.err();
}
