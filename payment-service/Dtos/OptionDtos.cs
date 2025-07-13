namespace payment_service.Dtos;

public class MongoSettings
{
    public string ConnectionString { get; set; }
    public string DatabaseName { get; set; }
    public string UserCollectionName { get; set; }
    public string PaymentCollectionName { get; set; }
}

public class StripeSettings
{
    public string WebhookSecret { get; set; }
    public string SecretKey { get; set; }
    public string Currency { get; set; }
}

public class RateSettings
{
    public decimal CreditsPerUsd { get; set; }
}

public class ServiceSettings
{
    public string AiServiceUrl { get; set; }
}