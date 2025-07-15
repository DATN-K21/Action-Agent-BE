using MongoDB.Driver;
using payment_service.Dtos;
using payment_service.Services;
using Stripe;

namespace payment_service.Extensions;

public static class ServiceExtensions
{
    public static IServiceCollection RegisterOptions(this IServiceCollection services, IConfiguration configuration)
    {
        services.Configure<MongoSettings>(configuration.GetSection(nameof(MongoSettings)));
        services.Configure<StripeSettings>(configuration.GetSection(nameof(StripeSettings)));
        services.Configure<RateSettings>(configuration.GetSection(nameof(RateSettings)));
        services.Configure<ServiceSettings>(configuration.GetSection(nameof(ServiceSettings)));
        return services;
    }
    
    public static IServiceCollection RegisterServices(this IServiceCollection services, IConfiguration configuration)
    {
        var mongoSettings = configuration.GetSection(nameof(MongoSettings)).Get<MongoSettings>()!;
        var mongoClient = new MongoClient(mongoSettings.ConnectionString);
        var mongoDatabase = mongoClient.GetDatabase(mongoSettings.DatabaseName);
        services.AddSingleton(mongoDatabase);

        StripeConfiguration.ApiKey = configuration.GetValue<string>(nameof(StripeSettings.SecretKey));
        services.AddScoped<IPaymentService, PaymentService>();
        
        return services;
    }
}