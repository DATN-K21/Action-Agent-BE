using payment_service.Endpoints.v1;
using payment_service.Extensions;

var builder = WebApplication.CreateBuilder(args);

builder.Services
    .RegisterOptions(builder.Configuration)
    .RegisterServices(builder.Configuration);

var app = builder.Build();
app.MapPaymentEndpoints();

app.Run();