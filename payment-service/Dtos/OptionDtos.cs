namespace payment_service.Dtos;

public record MongoSettings
(
    string ConnectionString = "<your-connection-string>",
    string DatabaseName = "user-database",
    string UserCollectionName = "users",
    string PaymentCollectionName = "payments"
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