using MongoDB.Driver;
using payment_service.Dtos;
using payment_service.Services;
using Stripe;

namespace payment_service.Extensions;

public static class ServiceExtensions
{
    public static IServiceCollection RegisterOptions(this IServiceCollection services, IConfiguration configuration)
    {
        services.Configure<MongoSettings>(configuration.GetSection("MongoSettings"));
        services.Configure<StripeSettings>(configuration.GetSection("StripeSettings"));
        services.Configure<RateSettings>(configuration.GetSection("RateSettings"));
        return services;
    }
    
    public static IServiceCollection RegisterServices(this IServiceCollection services, IConfiguration configuration)
    {
        var mongoSettings = configuration.GetSection("MongoSettings").Get<MongoSettings>()!;
        var mongoClient = new MongoClient(mongoSettings.ConnectionString);
        var mongoDatabase = mongoClient.GetDatabase(mongoSettings.DatabaseName);
        services.AddSingleton(mongoDatabase);

        StripeConfiguration.ApiKey = configuration.GetValue<string>("StripeSettings:SecretKey");
        
        services.AddScoped<IPaymentService, PaymentService>();
        
        return services;
    }
}