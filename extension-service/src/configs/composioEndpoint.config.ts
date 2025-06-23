import { EnvironmentConfig } from "./environment.config";

export class ComposioEndpointConfig {
  static readonly COMPOSIO_APP_ENDPOINT: string = `${EnvironmentConfig.COMPOSIO_API_BASE_URL}/v1/apps`;
	static readonly COMPOSIO_ACTION_ENDPOINT: string = `${EnvironmentConfig.COMPOSIO_API_BASE_URL}/v2/actions`;
}