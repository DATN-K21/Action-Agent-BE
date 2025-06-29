namespace speech_recognition.Services;

public interface ISpeechRecognition
{
    Task<string> FromFile(IFormFile audioFile);
}