namespace payment_service.Dtos.Payment;

public record ConfirmPaymentResponse
(
    int Status,
    bool Data,
    string? Message = null
) : BaseResponse<bool>(Status, Data, Message);