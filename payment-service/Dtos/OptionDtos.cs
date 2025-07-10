namespace payment_service.Dtos;

public record MongoSettings
(
    string ConnectionString = "mongodb://root:root@localhost:27017/user-service?authSource=admin",
    string DatabaseName = "user-service",
    string UserCollectionName = "Users",
    string PaymentCollectionName = "Payments"
);

public record StripeSettings
(
    string WebhookSecret = "<your-webhook-secret>",
    string SecretKey = "<your-secret-key>",
    string Currency = "usd"
);

public record RateSettings
(
    decimal CreditsPerUsd = 10000m
);