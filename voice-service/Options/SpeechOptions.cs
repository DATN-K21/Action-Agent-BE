using Newtonsoft.Json;
using System;
using System.Text;

namespace speech_recognition.Options;

public class SpeechOptions
{ 
    public GoogleCredentialConfig GoogleCredential { get; set; } = new();
    
    public const string Options= "SpeechOptions";
}

public class GoogleCredentialConfig
{
    [JsonProperty("type")]
    public string Type { get; set; } = string.Empty;

    [JsonProperty("project_id")]
    public string ProjectId { get; set; } = string.Empty;

    [JsonProperty("private_key_id")]
    public string PrivateKeyId { get; set; } = string.Empty;

    [JsonProperty("client_email")]
    public string ClientEmail { get; set; } = string.Empty;

    [JsonProperty("client_id")]
    public string ClientId { get; set; } = string.Empty;

    [JsonProperty("auth_uri")]
    public string AuthUri { get; set; } = string.Empty;

    [JsonProperty("token_uri")]
    public string TokenUri { get; set; } = string.Empty;

    [JsonProperty("auth_provider_x509_cert_url")]
    public string AuthProviderX509CertUrl { get; set; } = string.Empty;

    [JsonProperty("client_x509_cert_url")]
    public string ClientX509CertUrl { get; set; } = string.Empty;

    [JsonProperty("universe_domain")]
    public string UniverseDomain { get; set; } = string.Empty;

    [JsonIgnore]
    public string PrivateKey { get; set; } = string.Empty;

    [JsonProperty("private_key")]
    public string GetDecodedPrivateKey => Encoding.UTF8.GetString(Convert.FromBase64String(PrivateKey));
}