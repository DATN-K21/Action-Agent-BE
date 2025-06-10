using Microsoft.AspNetCore.Mvc;

namespace speech_recognition.Models;

public class AudioUploadRequest
{
    [FromForm(Name = "audioFile")]
    public IFormFile AudioFile { get; set; } = default!;

}