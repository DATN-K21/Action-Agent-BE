using Google.Cloud.Speech.V1;
using Microsoft.Extensions.Options;
using speech_recognition.Helpers;
using speech_recognition.Options;

namespace speech_recognition.Services;

public class SpeechRecognition : ISpeechRecognition
{
    private readonly ILogger<SpeechRecognition> _logger;

    public SpeechRecognition(ILogger<SpeechRecognition> logger, IOptions<SpeechOptions> options)
    {
        _logger = logger;
        var speechOptions = options.Value;
        
        var fullPath = Path.Combine(Directory.GetCurrentDirectory(), speechOptions.GoogleApplicationCredentials);
        Environment.SetEnvironmentVariable("GOOGLE_APPLICATION_CREDENTIALS", fullPath);
    }

public async Task<string> FromFile(IFormFile audioFile)
{
    const string methodName = $"{nameof(SpeechRecognition)}.{nameof(FromFile)} =>";
    _logger.LogInformation("{Method} Start processing audio file: {FileName}, Size: {FileSize} bytes", methodName, audioFile.FileName, audioFile.Length);
    
    
    var speech = await SpeechClient.CreateAsync();

    var config = new RecognitionConfig
    {
        // Encoding = RecognitionConfig.Types.AudioEncoding.Linear16,
        LanguageCode = "en-US",
        AlternativeLanguageCodes = { "vi-VN" },
        Model = "default"
    };
    
    byte[] bytes= await AudioHelper.ConvertIFormFileToByteArrayAsync(audioFile);

    RecognitionAudio audios = RecognitionAudio.FromBytes(bytes);

    try
    {
        RecognizeResponse response = await speech.RecognizeAsync(config, audios);
        if (response.Results.Count != 0)
        {
            _logger.LogInformation(
                "{Method} Speech recognized successfully: {Transcript}", methodName,
                response.Results[0].Alternatives[0].Transcript
            );
            return response.Results[0].Alternatives[0].Transcript;
        }
    }
    catch (InvalidOperationException e)
    {
        _logger.LogError("{Method} Error during speech recognition: {ErrorMessage}", methodName, e.Message);
        return string.Empty;
    }
    catch (Exception e)
    {
        _logger.LogError("{Method} Unexpected error: {ErrorMessage}", methodName, e.Message);
        return string.Empty;
    }
   
    
    return string.Empty;
    


}
}


