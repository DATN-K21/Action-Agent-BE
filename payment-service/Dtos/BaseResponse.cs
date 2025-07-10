namespace payment_service.Dtos;

/// <summary>
/// Generic base response record.
/// </summary>
/// <typeparam name="T">Type of the Data payload.</typeparam>
public record BaseResponse<T>(
    int Status,
    T? Data,
    string? Message
);

