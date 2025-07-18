using payment_service.Endpoints.v1;
using payment_service.Extensions;
using Prometheus;

var builder = WebApplication.CreateBuilder(args);

builder.Services
    .RegisterOptions(builder.Configuration)
    .RegisterServices(builder.Configuration)
    .AddMetricServer(options =>
    {
        options.Port = 9090; // Default port for Prometheus metrics
    });

var app = builder.Build();
app.UseMetricServer();
app.UseHttpMetrics();
app.MapPaymentEndpoints();

app.Run();