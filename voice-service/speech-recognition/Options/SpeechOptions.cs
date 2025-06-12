namespace speech_recognition.Options;

public class SpeechOptions
{
    public string Endpoint { get; set; } = string.Empty;
    public string SubscriptionKey { get; set; } = string.Empty;

    public string[] SupportedLanguages { get; set; } = Array.Empty<string>();
    
    public string GoogleApplicationCredentials { get; set; } = string.Empty;
}