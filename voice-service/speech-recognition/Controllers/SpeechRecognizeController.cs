using Microsoft.AspNetCore.Mvc;
using speech_recognition.Exceptions;
using speech_recognition.Models;
using speech_recognition.Responses;
using speech_recognition.Services;

namespace speech_recognition.Controllers;

[ApiController]
[Route("api/v1/")]
public class SpeechRecognizeController : ControllerBase
{
    private readonly ISpeechRecognition _speechRecognition;

    public SpeechRecognizeController(ISpeechRecognition speechRecognition)
    {
        _speechRecognition = speechRecognition;
    }

    [HttpPost("recognize")]
    public async Task<BaseResponse> RecognizeSpeech([FromForm] AudioUploadRequest? request)
    {
        var response = new BaseResponse<string>();

        var audioFile = request?.AudioFile;
        if (audioFile == null || audioFile.Length == 0)
            return response.ToBadRequestResponse("No audio file provided.");

        if (!Path.GetExtension(audioFile.FileName).Equals(".webm", StringComparison.CurrentCultureIgnoreCase))
        {
            throw new BadRequestException("Invalid file format", "Only .wav files are supported for speech recognition.");;
        }

        var result = await _speechRecognition.FromFile(audioFile);

        if (string.IsNullOrEmpty(result))
            throw new BadRequestException("No speech recognized in the provided audio file.");

        return response.ToSuccessResponse(result, "Speech recognized successfully.");
    }

}