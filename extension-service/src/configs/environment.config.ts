import * as dotenv from 'dotenv';

dotenv.config();

export class EnvironmentConfig {
  static readonly PORT: number = Number(process.env.PORT) || 15300;
  static readonly COMPOSIO_API_BASE_URL: string = process.env.COMPOSIO_API_BASE_URL || '';
  static readonly DATABASE_URL: string = process.env.DATABASE_URL || '';
  static readonly COMPOSIO_API_KEY: string = process.env.COMPOSIO_API_KEY || '';
  // Add more environment variables as needed
}