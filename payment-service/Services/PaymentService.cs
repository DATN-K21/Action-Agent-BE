using Microsoft.Extensions.Options;
using MongoDB.Bson;
using MongoDB.Driver;
using payment_service.Dtos;
using Stripe;
using payment_service.Models;
using payment_service.Dtos.Payment;

namespace payment_service.Services;

public class PaymentService : IPaymentService
{
    private readonly ILogger<PaymentService> _logger;
    private readonly IMongoCollection<User> _userCollection;
    private readonly IMongoCollection<Payment> _paymentCollection;
    private readonly PaymentIntentService _stripeIntentService;
    private readonly StripeSettings _stripeSettings;
    private readonly RateSettings _rateSettings;
    public PaymentService
    (
        ILogger<PaymentService> logger,
        IMongoDatabase db,
        IOptions<MongoSettings> mongoOptions,
        IOptions<StripeSettings> stripeOptions,
        IOptions<RateSettings> rateOptions
    )
    {
        _logger = logger;

        // collections: users & payments
        _userCollection = db.GetCollection<User>(mongoOptions.Value.UserCollectionName);
        _paymentCollection = db.GetCollection<Payment>(mongoOptions.Value.PaymentCollectionName);

        _stripeSettings = stripeOptions.Value;
        _rateSettings = rateOptions.Value;

        StripeConfiguration.ApiKey = _stripeSettings.SecretKey;
        _stripeIntentService = new PaymentIntentService();
    }

    /// <summary>
    /// Create a new PaymentIntent for the user and record a Payment doc
    /// </summary>
    public async Task<CreatePaymentIntentResponse> CreatePaymentIntentAsync(string userId, decimal amountUsd)
    {
        var fn = $"{nameof(PaymentService)}.{nameof(CreatePaymentIntentAsync)} UserId={userId}, AmountUsd={amountUsd}";
        _logger.LogInformation(fn);

        try
        {
            var validation = await ValidateUserExistsAsync(userId, amountUsd);
            if (validation is not null)
                return validation;

            // 1) create Stripe PaymentIntent
            var piOptions = new PaymentIntentCreateOptions
            {
                Amount = (long)(amountUsd * 100),
                Currency = _stripeSettings.Currency,
                PaymentMethodTypes = new List<string> { "card" }
            };

            var idempotencyKey = $"{userId}-{Guid.NewGuid()}";
            var requestOptions = new RequestOptions { IdempotencyKey = idempotencyKey };

            var intent = await _stripeIntentService.CreateAsync(piOptions, requestOptions);
            _logger.LogInformation("{Fn} => Created PaymentIntent {Id}", fn, intent.Id);

            // 2) record Payment document (status = created)
            var payment = new Payment
            {
                PaymentIntentId = intent.Id,
                UserId = ObjectId.Parse(userId),
                AmountUsd = amountUsd,
                Credits = 0,
                Status = PaymentStatus.Created,
            };
            await _paymentCollection.InsertOneAsync(payment);

            var data = new PaymentIntentData(intent.ClientSecret, intent.Id);
            return new CreatePaymentIntentResponse(200, data, "Payment intent created successfully");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "{Fn} => ERROR: {Msg}", fn, ex.Message);
            return new CreatePaymentIntentResponse(500, null, "Internal server error");
        }
    }

    /// <summary>
    /// Confirm a PaymentIntent when webhook arrives, credit user & update Payment doc
    /// </summary>
    public async Task<ConfirmPaymentResponse> ConfirmPaymentAsync(string paymentIntentId)
    {
        var fn = $"{nameof(PaymentService)}.{nameof(ConfirmPaymentAsync)} IntentId={paymentIntentId}";
        _logger.LogInformation(fn);

        try
        {
            // 1) fetch stored payment
            var payment = await _paymentCollection
                .Find(p => p.PaymentIntentId == paymentIntentId)
                .FirstOrDefaultAsync();

            if (payment is null)
                return new ConfirmPaymentResponse(404, false, "Payment record not found");

            if (payment.Status == PaymentStatus.Confirmed || payment.Status == PaymentStatus.Refunded)
                return new ConfirmPaymentResponse(200, true, "Already confirmed or refunded");

            // 2) retrieve intent from Stripe
            var intent = await _stripeIntentService.GetAsync(paymentIntentId);
            if (!string.Equals(intent.Status, "succeeded", StringComparison.OrdinalIgnoreCase))
                return new ConfirmPaymentResponse(400, false, "PaymentIntent not succeeded");

            // 3) calculate credits and update user balance
            var amountUsd = intent.AmountReceived / 100m;
            var creditsToAdd = (long)(amountUsd * _rateSettings.CreditsPerUsd);

            var userFilter = Builders<User>.Filter.Eq(u => u.Id, payment.UserId);
            var userUpdate = Builders<User>.Update.Inc(u => u.Balance, creditsToAdd);
            await _userCollection.UpdateOneAsync(userFilter, userUpdate);

            // 4) update Payment doc
            var paymentFilter = Builders<Payment>.Filter.Eq(p => p.Id, payment.Id);
            var paymentUpdate = Builders<Payment>.Update
                .Set(p => p.Credits, creditsToAdd)
                .Set(p => p.Status, PaymentStatus.Confirmed)
                .Set(p => p.UpdatedAt, DateTime.UtcNow);
            await _paymentCollection.UpdateOneAsync(paymentFilter, paymentUpdate);

            _logger.LogInformation("{Fn} => Confirmed. Credits={Credits}", fn, creditsToAdd);
            return new ConfirmPaymentResponse(200, true, "Payment confirmed successfully");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "{Fn} => ERROR: {Msg}", fn, ex.Message);
            return new ConfirmPaymentResponse(500, false, "Internal server error");
        }
    }

    #region Helpers

    private async Task<CreatePaymentIntentResponse?> ValidateUserExistsAsync(string userId, decimal amountUsd)
    {
        if (string.IsNullOrWhiteSpace(userId))
            return new CreatePaymentIntentResponse(400, null, "UserId cannot be empty");
        if (amountUsd <= 0)
            return new CreatePaymentIntentResponse(400, null, "Amount must be > 0");
        if (!ObjectId.TryParse(userId, out var oid))
            return new CreatePaymentIntentResponse(400, null, "Invalid UserId format");
        var user = await _userCollection.Find(u => u.Id == oid).FirstOrDefaultAsync();
        if (user is null)
            return new CreatePaymentIntentResponse(404, null, "User not found");
        return null;
    }

    #endregion
}
