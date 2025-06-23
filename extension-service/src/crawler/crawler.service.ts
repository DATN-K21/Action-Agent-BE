import { ComposioEndpointConfig } from '@/configs/composioEndpoint.config';
import { EnvironmentConfig } from '@/configs/environment.config';
import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import axios from 'axios';
import { Model, Types } from 'mongoose';
import { Action, ActionDocument } from '../actions/schema/action.schema';
import { App, AppDocument } from '../apps/schema/apps.schema';

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

    // 3. For each app, fetch details and actions, then save
    // Keep the order of apps as they are in the response
    for (let index = 0; index < apps.items.length; index++) {
      const app = apps.items[index];
      const progressHeaderText = `${index + 1}/${totalApps}. `;
      console.log(`[CRAWL] ${progressHeaderText}Crawling app: ${app?.key}`);
      try {
        // Fetch app detail
        const appDetail = await this.fetchWithRetry(`${ComposioEndpointConfig.COMPOSIO_APP_ENDPOINT}/${app.key}`);
        let appActionsNumber = 0;

        // Fetch actions for this app
        const actionsRes = await this.fetchWithRetry(`${ComposioEndpointConfig.COMPOSIO_ACTION_ENDPOINT}/list/all?apps=${app.key}`);
        console.log(`[CRAWL] ${progressHeaderText}${actionsRes.items?.length || 0} actions found for app ${app.key}.`);
        if (actionsRes.items) {
          appActionsNumber = actionsRes.items.length;
          await Promise.all(
            actionsRes.items.map(async (action: any, i: number) => {
              const fetchedAction = await this.fetchWithRetry(`${ComposioEndpointConfig.COMPOSIO_ACTION_ENDPOINT}/${action.enum}`);
              console.log(`[CRAWL] ${progressHeaderText}Processing action ${i + 1}/${actionsRes.items.length}: ${action.enum}`);
              await this.actionModel.updateOne(
                { enum: action.enum },
                { 
                  $set: { 
                    ...fetchedAction,
                    appKey: app.key ?? fetchedAction?.appId,
                    availableVersions: fetchedAction?.availableVersions ?? fetchedAction?.available_versions,
                    noAuth: fetchedAction?.noAuth ?? fetchedAction?.no_auth,
                  },
                  $setOnInsert: { id: new Types.ObjectId() },
                },
                { upsert: true }
              );
            })
          );
        }
        // Save app to DB (upsert)
        await this.appModel.updateOne(
          { key: app.key },
          {
            $set: {
              ...appDetail,
              actionsCount: appActionsNumber,
              noAuth: appDetail?.noAuth ?? appDetail?.no_auth,
              isCustomApp: appDetail?.meta?.isCustomApp ?? appDetail?.meta?.is_custom_app,
              triggerCount: appDetail?.meta?.triggerCount ?? appDetail?.meta?.trigger_count,
            },
            $setOnInsert: { id: new Types.ObjectId() },
          },
          { upsert: true }
        );
        console.log(`[CRAWL] ${progressHeaderText} DONE.\n----------------------------------------------------`);
      } catch (err) {
        console.error(`Failed to crawl app ${app.key}: ${err.message}`);
      }
    }

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