from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def set_custom_openapi(app: FastAPI) -> FastAPI:
    """Set custom OpenAPI schema."""

    def custom_openapi():
        if not app.openapi_schema:
            app.openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                openapi_version=app.openapi_version,
                description=app.description,
                terms_of_service=app.terms_of_service,
                contact=app.contact,
                license_info=app.license_info,
                routes=app.routes,
                tags=app.openapi_tags,
                servers=app.servers,
            )

            # Ensure "components" exists in OpenAPI schema
            if "components" not in app.openapi_schema:
                app.openapi_schema["components"] = {}

            # Ensure "schemas" exists inside "components"
            if "schemas" not in app.openapi_schema["components"]:
                app.openapi_schema["components"]["schemas"] = {}

            # Define security scheme for Swagger authorization
            security_schemes = {
                "UserAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "x-user-id",
                    "description": "User ID required for authorization",
                },
                "RoleAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "x-user-role",
                    "description": "User role required for authorization",
                },
                "EmailAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "x-user-email",
                    "description": "User role required for authorization",
                },
            }

            app.openapi_schema["components"]["securitySchemes"] = security_schemes

            # Apply security requirements to all routes
            for path, methods in app.openapi_schema.get("paths", {}).items():
                for method, details in methods.items():
                    responses = details.get("responses", {})
                    if "422" in responses:
                        del responses["422"]  # Remove default 422 response

                    # Apply security requirements to all endpoints
                    details["security"] = [{"UserAuth": [], "RoleAuth": [], "EmailAuth": []}]

        return app.openapi_schema

    app.openapi = custom_openapi  # Assign the function to app.openapi
    return app
