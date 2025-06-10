using Microsoft.CognitiveServices.Speech.Audio;
using NAudio.Wave;

namespace speech_recognition.Helpers;

public static class AudioHelper
{
    public static Stream ConvertToWav(Stream inputStream)
    {
        var outStream = new MemoryStream(); // đừng dùng `using` ở đây

        using var mp3Reader = new Mp3FileReader(inputStream);
        var wavFormat = new WaveFormat(16000, 16, 1); // 16kHz, 16bit, mono
        using var pcmStream = new WaveFormatConversionStream(wavFormat, mp3Reader);

        WaveFileWriter.WriteWavFileToStream(outStream, pcmStream);
        outStream.Position = 0;

        return outStream; // vẫn còn sống
    }


    public static async Task<byte[]> ConvertToPcmWavAsync(Stream inputStream)
    {
        await using var reader = new WaveFileReader(inputStream);

        var targetFormat = new WaveFormat(16000, 16, 1); // 16kHz, 16-bit, mono

        using var resampler = new MediaFoundationResampler(reader, targetFormat);
        resampler.ResamplerQuality = 60; // 1-60 (higher = better quality)

        using var outputStream = new MemoryStream();
        WaveFileWriter.WriteWavFileToStream(outputStream, resampler);
        return outputStream.ToArray(); // ready to push to Azure
    }

    
    public static BinaryAudioStreamReader CreateBinaryFileReader(string filename)
    {
        BinaryReader reader = new BinaryReader(File.OpenRead(filename));
        return new BinaryAudioStreamReader(reader);
    }
}

public sealed class BinaryAudioStreamReader : PullAudioInputStreamCallback
    {
        private System.IO.BinaryReader _reader;

        /// <summary>
        /// Creates and initializes an instance of BinaryAudioStreamReader.
        /// </summary>
        /// <param name="reader">The underlying stream to read the audio data from. Note: The stream contains the bare sample data, not the container (like wave header data, etc).</param>
        public BinaryAudioStreamReader(System.IO.BinaryReader reader)
        {
            _reader = reader;
        }

        /// <summary>
        /// Creates and initializes an instance of BinaryAudioStreamReader.
        /// </summary>
        /// <param name="stream">The underlying stream to read the audio data from. Note: The stream contains the bare sample data, not the container (like wave header data, etc).</param>
        public BinaryAudioStreamReader(System.IO.Stream stream)
            : this(new System.IO.BinaryReader(stream))
        {
        }

        /// <summary>
        /// Reads binary data from the stream.
        /// </summary>
        /// <param name="dataBuffer">The buffer to fill</param>
        /// <param name="size">The size of data in the buffer.</param>
        /// <returns>The number of bytes filled, or 0 in case the stream hits its end and there is no more data available.
        /// If there is no data immediate available, Read() blocks until the next data becomes available.</returns>
        public override int Read(byte[] dataBuffer, uint size)
        {
            return _reader.Read(dataBuffer, 0, (int)size);
        }

        /// <summary>
        /// This method performs cleanup of resources.
        /// The Boolean parameter <paramref name="disposing"/> indicates whether the method is called from <see cref="IDisposable.Dispose"/> (if <paramref name="disposing"/> is true) or from the finalizer (if <paramref name="disposing"/> is false).
        /// Derived classes should override this method to dispose resource if needed.
        /// </summary>
        /// <param name="disposing">Flag to request disposal.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposed)
            {
                return;
            }

            if (disposing)
            {
                _reader.Dispose();
            }

            disposed = true;
            base.Dispose(disposing);
        }

        private bool disposed = false;
    }