namespace payment_service.Dtos.Payment;

public record CreatePaymentIntentRequest
(
    string UserId,
    decimal AmountUsd
);

public record CreatePaymentIntentResponse
(
    int Status,
    PaymentIntentData? Data,
    string? Message = null
) : BaseResponse<PaymentIntentData>(Status, Data, Message);

public record PaymentIntentData
(
    string ClientSecret,
    string PaymentIntentId
);