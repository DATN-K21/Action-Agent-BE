using Microsoft.CognitiveServices.Speech;
using Microsoft.CognitiveServices.Speech.Audio;
using Microsoft.Extensions.Options;
using speech_recognition.Helpers;
using speech_recognition.Options;

namespace speech_recognition.Services;

public class SpeechRecognition(ILogger<SpeechRecognition> logger, IOptions<SpeechOptions> options)
    : ISpeechRecognition
{
    private readonly SpeechOptions _speechOptions = options.Value;

    public async Task<string> FromFile(IFormFile audioFile)
    {
        const string methodName = $"{nameof(SpeechRecognition)}.{nameof(FromFile)} =>";
        logger.LogInformation(methodName);

        var config = SpeechConfig.FromEndpoint(new Uri(_speechOptions.Endpoint), _speechOptions.SubscriptionKey);
        var autoDetectSourceLanguageConfig =
            AutoDetectSourceLanguageConfig.FromLanguages(_speechOptions.SupportedLanguages);

        var stopRecognition = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);

        string resultText = string.Empty;

        using (var pushStream =
               AudioInputStream.CreatePushStream(
                   AudioStreamFormat.GetWaveFormatPCM(16000, 16, 1)
               )) // Assuming 16kHz, 16-bit mono PCM format))
        {
            using (var audioInput = AudioConfig.FromStreamInput(pushStream))
            {
                // Creates a speech recognizer 
                using (var recognizer = new SpeechRecognizer(config, autoDetectSourceLanguageConfig, audioInput))
                {
                    // Subscribes to events.
                    recognizer.Recognizing += (s, e) =>
                    {
                        logger.LogInformation($"RECOGNIZING: Text={e.Result.Text}");
                    };

                    recognizer.Recognized += (s, e) =>
                    {
                        if (e.Result.Reason == ResultReason.RecognizedSpeech)
                        {
                            logger.LogInformation($"RECOGNIZED: Text={e.Result.Text}");
                            resultText += e.Result.Text + " ";
                        }
                        else if (e.Result.Reason == ResultReason.NoMatch)
                        {
                            logger.LogWarning($"NOMATCH: Speech could not be recognized.");
                        }
                    };

                    recognizer.Canceled += (s, e) =>
                    {
                        logger.LogWarning($"CANCELED: Reason={e.Reason}");

                        if (e.Reason == CancellationReason.Error)
                        {
                            logger.LogError($"CANCELED: ErrorCode={e.ErrorCode}");
                        }

                        stopRecognition.TrySetResult(0);
                    };

                    recognizer.SessionStarted += (s, e) => { logger.LogInformation("\nSession started event."); };

                    recognizer.SessionStopped += (s, e) =>
                    {
                        logger.LogInformation("\nSession stopped event.");
                        stopRecognition.TrySetResult(0);
                    };

                    // Starts continuous recognition. Uses StopContinuousRecognitionAsync() to stop recognition.
                    await recognizer.StartContinuousRecognitionAsync().ConfigureAwait(false);

                    await using (var originalStream = audioFile.OpenReadStream())
                    {
                        var pcmBytes = await AudioHelper.ConvertToPcmWavAsync(originalStream);
                        pushStream.Write(pcmBytes, pcmBytes.Length);
                        pushStream.Close();
                    }

                    // Waits for completion.
                    // Use Task.WaitAny to keep the task rooted.
                    Task.WaitAny(new[] { stopRecognition.Task });

                    // Stops recognition.
                    await recognizer.StopContinuousRecognitionAsync().ConfigureAwait(false);
                }
            }
        }

        return string.IsNullOrEmpty(resultText)
            ? string.Empty
            : resultText.Trim();
    }
}