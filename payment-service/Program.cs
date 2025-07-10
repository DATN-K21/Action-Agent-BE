using MongoDB.Bson;
using MongoDB.Driver;
using Stripe;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var mongoConnection = builder.Configuration["MONGODB_CONNECTION_STRING"];
var mongoClient = new MongoClient(mongoConnection);
var mongoUrl = new MongoUrl(mongoConnection);
var database = mongoClient.GetDatabase(mongoUrl.DatabaseName);

StripeConfiguration.ApiKey = builder.Configuration["STRIPE_SECRET_KEY"];

var app = builder.Build();

app.UseSwagger();
app.UseSwaggerUI();

app.MapGet("/ping", () => Results.Ok(new { message = "pong" }));

app.MapPost("/api/v1/create-payment-intent", async (CreatePaymentIntentRequest request) =>
{
    var options = new PaymentIntentCreateOptions
    {
        Amount = (long)(request.Amount * 100),
        Currency = "usd",
        AutomaticPaymentMethods = new PaymentIntentAutomaticPaymentMethodsOptions { Enabled = true }
    };
    var service = new PaymentIntentService();
    var intent = await service.CreateAsync(options);
    return Results.Ok(new { clientSecret = intent.ClientSecret, paymentIntentId = intent.Id });
});

app.MapPost("/api/v1/confirm-payment", async (ConfirmPaymentRequest request) =>
{
    var service = new PaymentIntentService();
    var intent = await service.GetAsync(request.PaymentIntentId);
    if (intent.Status != "succeeded")
    {
        return Results.BadRequest(new { error = "Payment not completed" });
    }

    var users = database.GetCollection<BsonDocument>("Users");
    var filter = Builders<BsonDocument>.Filter.Eq("_id", ObjectId.Parse(request.UserId));
    var update = Builders<BsonDocument>.Update.Inc("balance", intent.Amount / 100.0);
    await users.UpdateOneAsync(filter, update, new UpdateOptions { IsUpsert = true });
    return Results.Ok(new { status = "updated" });
});

app.Run();

record CreatePaymentIntentRequest(string UserId, decimal Amount);
record ConfirmPaymentRequest(string UserId, string PaymentIntentId);