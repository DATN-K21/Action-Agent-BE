namespace speech_recognition.Helpers;

public static class AudioHelper
{
    public static async Task<byte[]> ConvertIFormFileToByteArrayAsync(IFormFile file)
    {
        using var memoryStream = new MemoryStream();
        await file.CopyToAsync(memoryStream);
        return memoryStream.ToArray();
    }

}