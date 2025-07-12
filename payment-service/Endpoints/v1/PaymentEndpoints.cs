using System.Text;
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
            HttpRequest request,
            [FromServices] IPaymentService paymentService,
            [FromBody] CreatePaymentIntentRequest req) =>
        {
            // Get x-user-id and x-user-role headers
            var userIdHeader = request.Headers["x-user-id"].FirstOrDefault();
            var userRoleHeader = request.Headers["x-user-role"].FirstOrDefault();
            bool isAdmin = userRoleHeader != null && string.Equals(userRoleHeader, "admin", StringComparison.OrdinalIgnoreCase);
            if (!isAdmin && (userIdHeader == null || userIdHeader != req.UserId))
            {
                return Results.StatusCode(403);
            }

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
            var json = await new StreamReader(request.Body, Encoding.UTF8).ReadToEndAsync();
            var webhookSecret = stripeOptions.Value.WebhookSecret;

            try
            {
                var signatureHeader = request.Headers["Stripe-Signature"];
                var stripeEvent = EventUtility.ConstructEvent(json, signatureHeader, webhookSecret, throwOnApiVersionMismatch: false);

                // 2. Handle only succeeded intents
                if (stripeEvent.Type == EventTypes.PaymentIntentSucceeded)
                {
                    // 3. Confirm the payment
                    var paymentIntent = stripeEvent.Data.Object as PaymentIntent;
                    var response = await paymentService.ConfirmPaymentAsync(paymentIntent!.Id);
                    return response.ToResponse();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error processing Stripe event: {ex.Message}");
                Console.WriteLine($"Request body: {json}");
                Console.WriteLine($"Signature header: {request.Headers["Stripe-Signature"]}");
                Console.WriteLine($"Webhook secret: {webhookSecret}");
                return new ConfirmPaymentResponse(200, false, "Invalid Stripe signature").ToResponse();
            }

            return new ConfirmPaymentResponse(200, true, "Event processed").ToResponse();
        });

        return app;
    }
}