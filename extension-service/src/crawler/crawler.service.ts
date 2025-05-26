import { ComposioEndpointConfig } from '@/configs/composioEndpoint.config';
import { EnvironmentConfig } from '@/configs/environment.config';
import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import axios from 'axios';
import { Model, Types } from 'mongoose';
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
    console.log('[CRAWL] START CRAWLING ...');
    const apps = await this.fetchWithRetry(ComposioEndpointConfig.COMPOSIO_APP_ENDPOINT);
    if (!apps || !apps.items) {
      console.error('[CRAWL] No apps found or invalid response structure');
      return;
    }
    const totalApps = apps.items.length;
    const startTimer = Date.now();
    console.log(`[CRAWL] ${totalApps} apps found.`);

    // 2. Limit concurrency to avoid rate limits (e.g., 5 at a time)
    const pLimit = await getPLimit();
    const limit = pLimit(5);

    // 3. For each app, fetch details and actions, then save
    await Promise.all(
      apps.items.map((app: any, index: number) =>
        limit(async () => {
          const progressHeaderText = `${index + 1}/${totalApps}. `;
          console.log(`[CRAWL] ${progressHeaderText}Crawling app: ${app?.key}`);
          try {
            // Fetch app detail (optional, if needed)
            const appDetail = await this.fetchWithRetry(`${ComposioEndpointConfig.COMPOSIO_APP_ENDPOINT}/${app.key}`);
            let appActionsNumber = 0;

            // Fetch actions for this app
            const actionsRes = await this.fetchWithRetry(`${ComposioEndpointConfig.COMPOSIO_ACTION_ENDPOINT}/list/all?apps=${app.key}`);
            console.log(`[CRAWL] ${progressHeaderText}${actionsRes.items?.length || 0} actions found for app ${app.key}.`);
            if (actionsRes.items) {
              appActionsNumber = actionsRes.items.length;
              for(let i = 0; i < actionsRes.items.length; i++) {
                console.log(`[CRAWL] ${progressHeaderText}Processing action ${i + 1}/${actionsRes.items.length}: ${actionsRes.items[i].enum}`);
                const action = actionsRes.items[i];

                // Save action to DB (upsert)
                await this.actionModel.updateOne(
                  { enum: action.enum },
                  { $set: { ...action, appKey: app.key } },
                  { upsert: true }
                );
              }
            }
            // Save app to DB (upsert)
            await this.appModel.updateOne(
              { key: app.key },
              {
                $set: {
                  ...appDetail,
                  actionsCount: appActionsNumber,
                },
                $setOnInsert: {
                  id: new Types.ObjectId(),
                },
              },
              { upsert: true }
            );
            console.log(`[CRAWL] ${progressHeaderText} DONE.\n----------------------------------------------------`);
          } catch (err) {
            console.error(`Failed to crawl app ${app.key}: ${err.message}`);
          }
        })
      )
    );
    console.log('[CRAWL] CRAWLING COMPLETED !!!');
    return {
      totalApps: totalApps,
      durationInSeconds: (Date.now() - startTimer) / 1000, // in seconds
    }
  }

  // Helper with retry, timeout, and error handling
  private async fetchWithRetry(url: string, retries = 3, timeout = 1000000): Promise<any> {
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const res = await axios.get(url, {
          headers: {
            'X-API-Key': EnvironmentConfig.COMPOSIO_API_KEY,
          },
          timeout: timeout
         });
        return res.data;
      } catch (err) {
        if (attempt === retries) {
          console.error(`[CRAWL] Failed to fetch ${url} after ${retries} attempts:`, err);
          throw err;
        };
        console.warn(`[CRAWL] Retrying ${url} (attempt ${attempt})`);
        await new Promise(res => setTimeout(res, 1000 * attempt)); // Exponential backoff
      }
    }
  }
}