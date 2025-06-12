using speech_recognition.Options;
using speech_recognition.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddOptions<SpeechOptions>()
    .BindConfiguration(nameof(SpeechOptions));

builder.Services.AddScoped<ISpeechRecognition, SpeechRecognition>();



var app = builder.Build();

// Configure the HTTP request pipeline.

app.UseSwagger();
app.UseSwaggerUI();

//Add ping route to check if the service is running
app.MapGet("/ping", () => "pong")
    .WithName("Ping")
    .WithSummary("Check if the service is running")
    .WithDescription("Returns 'pong' if the service is up and running.")
    .Produces<string>(StatusCodes.Status200OK);

app.MapControllers();

app.Run();
