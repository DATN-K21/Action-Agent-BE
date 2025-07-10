# Payment Service

This lightweight service handles payments using Stripe's test mode and updates user balances in MongoDB.

## Environment Variables
- `MONGODB_CONNECTION_STRING` – connection string to the user MongoDB database.
- `STRIPE_SECRET_KEY` – Stripe secret API key.
- `ASPNETCORE_HTTP_PORTS` – port the service listens on (default `15700`).

## API Endpoints
- `GET /ping` – health check.
- `POST /create-payment-intent` – body: `{ "userId": "<id>", "amount": <number> }`. Returns a Stripe `clientSecret` and `paymentIntentId`.
- `POST /confirm-payment` – body: `{ "userId": "<id>", "paymentIntentId": "<id>" }`. Verifies the payment and increases the user's `balance` field.

## Flow
1. The frontend calls API Gateway which proxies requests to the payment-service.
2. Frontend sends a `create-payment-intent` request to obtain a Stripe `clientSecret`.
3. Using Stripe.js on the frontend, the user completes the payment.
4. After payment succeeds, frontend calls `confirm-payment` with the returned `paymentIntentId`.
5. The service verifies the payment with Stripe and increments the `balance` field in the corresponding user document in MongoDB.

The user-service does not need to be aware of the balance field; payment-service directly updates the `Users` collection.