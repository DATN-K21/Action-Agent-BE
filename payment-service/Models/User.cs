using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace payment_service.Models;

[BsonIgnoreExtraElements]
public class User
{
    [BsonId]
    public ObjectId Id { get; set; }

    [BsonElement("balance")]
    [BsonRepresentation(BsonType.Int64)]
    public long Balance { get; set; }

    // ...
}