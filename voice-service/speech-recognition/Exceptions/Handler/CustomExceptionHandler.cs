
using FluentValidation;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;

namespace speech_recognition.Exceptions.Handler;

public class CustomExceptionHandler(ILogger<CustomExceptionHandler> logger) : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(HttpContext context, Exception exception, CancellationToken cancellationToken)
    {
        logger.LogError("Error Message: {Message}, Time of occurrence {time}", exception.Message, DateTime.UtcNow);

        (string Title, string Details, int StatusCode) details = exception switch
        {
            InternalServerException =>
            (
                exception.GetType().Name,
                exception.Message,
                context.Response.StatusCode = StatusCodes.Status500InternalServerError
            ),
            BadRequestException =>
            (
                exception.GetType().Name,
                exception.Message,
                context.Response.StatusCode = StatusCodes.Status400BadRequest
            ),
            ValidationException =>
            (
                exception.GetType().Name,
                exception.Message,
                context.Response.StatusCode = StatusCodes.Status400BadRequest
            ),
            NotFoundException =>
            (
                exception.GetType().Name,
                exception.Message,
                context.Response.StatusCode = StatusCodes.Status404NotFound
            ),
            _ =>
            (
                exception.GetType().Name,
                exception.Message,
                context.Response.StatusCode = StatusCodes.Status500InternalServerError
            )
        };

        var problemDetails = new ProblemDetails
        {
            Title = details.Title,
            Status = details.StatusCode,
            Detail = details.Details,
            Instance = context.Request.Path
        };

        problemDetails.Extensions.Add("traceId", context.TraceIdentifier);

        if (exception is ValidationException validationException)
        {
            problemDetails.Extensions.Add("errors", validationException.Errors);
        }

        await context.Response.WriteAsJsonAsync(problemDetails, cancellationToken: cancellationToken);

        return true;
    }
}