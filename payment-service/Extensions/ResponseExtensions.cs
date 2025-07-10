using System.Text.Json;
using payment_service.Dtos;

namespace payment_service.Extensions;

public static class ResponseExtensions
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = false
    };
    
    public static IResult ToResponse<T>(this BaseResponse<T> response)
    {
        return Results.Json(
            response,
            JsonOptions,
            "application/json",
            response.Status
        );
    }
}