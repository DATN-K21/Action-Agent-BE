using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Options;
using payment_service.Dtos;
using payment_service.Dtos.Payment;
using payment_service.Extensions;
using payment_service.Services;
using Stripe;

namespace payment_service.Endpoints.v1;

public static class PaymentEndpoints
{
    private const string EndpointPrefix = "/api/v1/payment";
    
    public static WebApplication MapPaymentEndpoints(this WebApplication app)
    {
        // Ping
        app.MapGet("/ping", () => Results.Ok(new { message = "pong" }));

        // Create PaymentIntent
        app.MapPost($"{EndpointPrefix}/create-intent", async (
            [FromServices] IPaymentService paymentService,
            [FromBody] CreatePaymentIntentRequest req) =>
        {
            var response = await paymentService.CreatePaymentIntentAsync(req.UserId, req.AmountUsd);
            return response.ToResponse();
        });

        // Confirm PaymentIntent via webhook
        app.MapPost($"{EndpointPrefix}/confirm", async (
            HttpRequest request,
            [FromServices] IPaymentService paymentService,
            [FromServices] IOptions<StripeSettings> stripeOptions) =>
        {
            // 1. Verify signature
            var json = await new StreamReader(request.Body).ReadToEndAsync();
            var signature = request.Headers["Stripe-Signature"];
            Event stripeEvent;
            try
            {
                stripeEvent = EventUtility.ConstructEvent(json, signature, stripeOptions.Value.WebhookSecret);
            }
            catch
            {
                return new ConfirmPaymentResponse(400, false, "Invalid Stripe signature").ToResponse();
            }

            // 2. Handle only succeeded intents
            if (stripeEvent.Type == EventTypes.PaymentIntentSucceeded && stripeEvent.Data.Object is PaymentIntent paymentIntent)
            {
                // 3. Confirm the payment
                var response = await paymentService.ConfirmPaymentAsync(paymentIntent.Id);
                return response.ToResponse();
            }

            return new ConfirmPaymentResponse(200, true, "Event processed").ToResponse();
        });

        return app;
    }
}