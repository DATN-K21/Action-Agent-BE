using System.Net;
using Microsoft.AspNetCore.Mvc;

namespace speech_recognition.Responses;

public class BaseResponse
{
    public int Status { get; set; }
    public string? Message { get; set; }
    
    public BaseResponse ToInternalErrorResponse(string message = "Internal Server Error")
    {
        Status = (int)HttpStatusCode.InternalServerError;
        Message = message;
        return this;
    }
    
    public BaseResponse ToBadRequestResponse(string message = "Bad Request")
    {
        Status = (int)HttpStatusCode.BadRequest;
        Message = message;
        return this;
    }
    
    public BaseResponse ToNotFoundResponse(string message = "Not Found")
    {
        Status = (int)HttpStatusCode.NotFound;
        Message = message;
        return this;
    }
    
    public BaseResponse ToUnauthorizedResponse(string message = "Unauthorized")
    {
        Status = (int)HttpStatusCode.Unauthorized;
        Message = message;
        return this;
    }
    
    public BaseResponse ToUnConfirmedEmailResponse(string message = "Email is not confirmed")
    {
        Status = 450;
        Message = message;
        return this;
    }
    
    public BaseResponse ToForbiddenResponse(string message = "Forbidden")
    {
        Status = (int)HttpStatusCode.Forbidden;
        Message = message;
        return this;
    }

    public BaseResponse ToSuccessResponse()
    {
        Status = (int)HttpStatusCode.OK;
        return this;
    }
    
    public ObjectResult ToObjectResult()
    {
        return new ObjectResult(this) { StatusCode = Status };
    }
}

public class BaseResponse<T>: BaseResponse where T : class
{
    public T? Data { get; set; }
    
    public BaseResponse<T> ToSuccessResponse(T? data, string? message = null)
    {
        Status = (int)HttpStatusCode.OK;
        Message = message;
        Data = data;
        return this;
    }
}