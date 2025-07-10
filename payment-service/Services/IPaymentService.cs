using payment_service.Dtos.Payment;

namespace payment_service.Services;

public interface IPaymentService
{
    Task<CreatePaymentIntentResponse> CreatePaymentIntentAsync(string userId, decimal amount);
    Task<ConfirmPaymentResponse> ConfirmPaymentAsync(string paymentIntentId);
}