import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import axios from 'axios';
import { Model } from 'mongoose';
import { Action, ActionDocument } from './actions/schema/action.schema';
import { App, AppDocument } from './apps/schema/apps.schema';
import { getPLimit } from './helpers/pLimit.helper';

const COMPOSIO_API_BASE = 'https://backend.composio.dev/api/v1';

@Injectable()
export class CrawlerService {
  private readonly logger = new Logger(CrawlerService.name);

  constructor(
    @InjectModel(App.name) private appModel: Model<AppDocument>,
    @InjectModel(Action.name) private actionModel: Model<ActionDocument>,
  ) {}

  async crawlAllAppsAndActions() {
    // 1. Fetch all apps
    const apps = await this.fetchWithRetry(`${COMPOSIO_API_BASE}/apps`);

    // 2. Limit concurrency to avoid rate limits (e.g., 5 at a time)
    const pLimit = await getPLimit();
    const limit = pLimit(5);

    // 3. For each app, fetch details and actions, then save
    await Promise.all(
      apps.items.map(app =>
        limit(async () => {
          try {
            // Fetch app detail (optional, if needed)
            const appDetail = await this.fetchWithRetry(`${COMPOSIO_API_BASE}/apps/${app.key}`);

            // Save app to DB (upsert)
            await this.appModel.updateOne(
              { key: app.key },
              { $set: appDetail },
              { upsert: true }
            );

            // Fetch actions for this app
            const actionsRes = await this.fetchWithRetry(`${COMPOSIO_API_BASE}/apps/${app.key}/actions`);
            if (actionsRes.items) {
              for (const action of actionsRes.items) {
                // Save action to DB (upsert)
                await this.actionModel.updateOne(
                  { enum: action.enum },
                  { $set: { ...action, appKey: app.key } },
                  { upsert: true }
                );
              }
            }
            this.logger.log(`Crawled app: ${app.key} with ${actionsRes.items?.length || 0} actions`);
          } catch (err) {
            this.logger.error(`Failed to crawl app ${app.key}: ${err.message}`);
          }
        })
      )
    );
    this.logger.log('Crawling completed!');
  }

  // Helper with retry, timeout, and error handling
  private async fetchWithRetry(url: string, retries = 3, timeout = 10000): Promise<any> {
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const res = await axios.get(url, { timeout });
        return res.data;
      } catch (err) {
        if (attempt === retries) throw err;
        this.logger.warn(`Retrying ${url} (attempt ${attempt})`);
        await new Promise(res => setTimeout(res, 1000 * attempt)); // Exponential backoff
      }
    }
  }
}