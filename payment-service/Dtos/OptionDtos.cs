namespace payment_service.Dtos;

public record MongoSettings
(
    string ConnectionString,
    string DatabaseName,
    string UserCollectionName,
    string PaymentCollectionName
);

public record StripeSettings
(
    string WebhookSecret,
    string SecretKey,
    string Currency
);

public record RateSettings
(
    decimal CreditsPerUsd
);