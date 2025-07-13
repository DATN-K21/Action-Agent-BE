using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace payment_service.Models;

public class Payment
{
    [BsonId]
    public ObjectId Id { get; set; }
        
    [BsonElement("payment_intent_id")]
    public string PaymentIntentId { get; set; } = null!;
    
    [BsonElement("user_id")]
    public string UserId { get; set; } = null!;
        
    [BsonElement("amount_usd")]
    public decimal AmountUsd { get; set; }
        
    [BsonElement("credits")]
    public long Credits { get; set; }
        
    [BsonElement("status")]
    public PaymentStatus Status { get; set; } = PaymentStatus.Created;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? UpdatedAt { get; set; }
}

public enum PaymentStatus
{
    Created,
    Confirmed,
    Failed,
    Refunded
}