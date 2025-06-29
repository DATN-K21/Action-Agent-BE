using Google.Cloud.Speech.V1;
using Microsoft.Extensions.Options;
using Newtonsoft.Json;
using speech_recognition.Exceptions;
using speech_recognition.Helpers;
using speech_recognition.Options;

namespace speech_recognition.Services;

public class SpeechRecognition : ISpeechRecognition
{
    private readonly ILogger<SpeechRecognition> _logger;
    
    private readonly SpeechClient _speechClient;
    
    public SpeechRecognition(ILogger<SpeechRecognition> logger, IOptions<SpeechOptions> options)
    {
        _logger = logger;
        var credentialOptions = options.Value.GoogleCredential;
        
        var jsonCredential = JsonConvert.SerializeObject(credentialOptions);

        var clientBuilder = new SpeechClientBuilder
        {
            JsonCredentials = jsonCredential
        };
        _speechClient = clientBuilder.Build(); 
    }

    public async Task<string> FromFile(IFormFile audioFile)
    {
        const string methodName = $"{nameof(SpeechRecognition)}.{nameof(FromFile)} =>";
        _logger.LogInformation("{Method} Start processing audio file: {FileName}, Size: {FileSize} bytes", methodName, audioFile.FileName, audioFile.Length);
        
        var config = new RecognitionConfig
        {
            Encoding = RecognitionConfig.Types.AudioEncoding.WebmOpus,
            SampleRateHertz = 48000,
            LanguageCode = "en-US",
            AlternativeLanguageCodes = { "vi-VN" },
            Model = "default"
        };
        
        byte[] bytes= await AudioHelper.ConvertIFormFileToByteArrayAsync(audioFile);

        RecognitionAudio audios = RecognitionAudio.FromBytes(bytes);

        try
        {
            RecognizeResponse response = await _speechClient.RecognizeAsync(config, audios);
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
            throw new InternalServerException( "Invalid operation during speech recognition.", e.Message);
        }
        catch (Exception e)
        {
            _logger.LogError("{Method} Unexpected error: {ErrorMessage}", methodName, e.Message);
            throw new InternalServerException("An unexpected error occurred during speech recognition.", e.Message);
        }
       
        return string.Empty;
        
    }
    
    
}


