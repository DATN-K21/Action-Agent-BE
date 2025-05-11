def sanitize_composio_app_data(data):
    """
    Sanitize the Composio app data to map keys for integration.
    """
    sanitized_data = {
        "app_id": data["appId"],
        "key": data["key"],
        "name": data["name"],
        "display_name": data["displayName"],
        "description": data["description"],
        "logo": data["logo"],
        "categories": data["categories"],
        "tags": data["tags"],
        "enabled": data["enabled"],
        "created_at": data["createdAt"],
        "updated_at": data["updatedAt"],
        "no_auth": data["no_auth"],
        "meta": {
            "is_custom_app": data["meta"]["is_custom_app"] if "is_custom_app" in data["meta"] else False,
            "trigger_count": int(data["meta"]["triggerCount"]) if "triggerCount" in data["meta"] else 0,
            "actions_count": int(data["meta"]["actionsCount"]) if "actionsCount" in data["meta"] else 0,
        },
    }
    return sanitized_data
