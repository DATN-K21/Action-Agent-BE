import { ComposioEndpointConfig } from '@/configs/composioEndpoint.config';
import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import axios from 'axios';
import { Model } from 'mongoose';
import { Action, ActionDocument } from '../actions/schema/action.schema';
import { App, AppDocument } from '../apps/schema/apps.schema';
import { getPLimit } from '../helpers/pLimit.helper';

@Injectable()
export class CrawlerService {

  constructor(
    @InjectModel(App.name) private appModel: Model<AppDocument>,
    @InjectModel(Action.name) private actionModel: Model<ActionDocument>,
  ) {}

  async crawlAllAppsAndActions() {
    // 1. Fetch all apps
    console.log('START CRAWLING ...');
    const apps = await this.fetchWithRetry(ComposioEndpointConfig.COMPOSIO_APP_ENDPOINT);
    if (!apps || !apps.items) {
      console.error('No apps found or invalid response structure');
      return;
    }
    const totalApps = apps.items.length;
    console.log(`${totalApps} apps found.`);

    // 2. Limit concurrency to avoid rate limits (e.g., 5 at a time)
    const pLimit = await getPLimit();
    const limit = pLimit(5);

    // 3. For each app, fetch details and actions, then save
    await Promise.all(
      apps.items.map((app: any, index: number) =>
        limit(async () => {
          const progressHeaderText = `${index + 1}/${totalApps}. `;
          console.log(`${progressHeaderText}Crawling app: ${app?.key}`);
          try {
            // Fetch app detail (optional, if needed)
            const appDetail = await this.fetchWithRetry(`${ComposioEndpointConfig.COMPOSIO_APP_ENDPOINT}/${app.key}`);

            // Save app to DB (upsert)
            await this.appModel.updateOne(
              { key: app.key },
              { $set: appDetail },
              { upsert: true }
            );
            console.log(`${progressHeaderText}${app.key} app saved. Crawling its actions...`);

            // Fetch actions for this app
            const actionsRes = await this.fetchWithRetry(ComposioEndpointConfig.COMPOSIO_ACTION_ENDPOINT);
            console.log(`${progressHeaderText}${actionsRes.items?.length || 0} actions found for app ${app.key}.`);
            if (actionsRes.items) {
              for(let i = 0; i < actionsRes.items.length; i++) {
                console.log(`${progressHeaderText}Processing action ${i + 1}/${actionsRes.items.length}: ${actionsRes.items[i].enum}`);
                const action = actionsRes.items[i];

                // Save action to DB (upsert)
                await this.actionModel.updateOne(
                  { enum: action.enum },
                  { $set: { ...action, appKey: app.key } },
                  { upsert: true }
                );
              }
            }
            console.log(`${progressHeaderText} DONE.\n----------------------------------------------------`);
          } catch (err) {
            console.error(`Failed to crawl app ${app.key}: ${err.message}`);
          }
        })
      )
    );
    console.log('CRAWLING COMPLETED !!!');
  }

  // Helper with retry, timeout, and error handling
  private async fetchWithRetry(url: string, retries = 3, timeout = 10000): Promise<any> {
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const res = await axios.get(url, { timeout });
        return res.data;
      } catch (err) {
        if (attempt === retries) {
          console.error(`Failed to fetch ${url} after ${retries} attempts:`, err);
          throw err;
        };
        console.warn(`Retrying ${url} (attempt ${attempt})`);
        await new Promise(res => setTimeout(res, 1000 * attempt)); // Exponential backoff
      }
    }
  }
}