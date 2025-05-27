import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { Action } from './schema/action.schema';

@Injectable()
export class ActionsService {

	constructor(
		@InjectModel(Action.name) private readonly actionModel: Model<Action>,
	) {}

	async getAllActions(appKey: string): Promise<{result: Action[]; meta: { total: number }}> {
		if (!appKey) {
			throw new Error('App key is required');
		}

		const actions = await this.actionModel.find({ appKey }).exec();
		if (!actions || actions.length === 0) {
			throw new Error(`No actions found for app with key: ${appKey}`);
		}

		return {
			result: actions,
			meta: {
				total: actions.length,
			}
		}
	}

	async getActionByEnum(actionEnum: string, appKey: string): Promise<Action> {
		if (!actionEnum || !appKey) {
			throw new Error('Action enum and app key are required');
		}

		const action = await this.actionModel.findOne({ enum: actionEnum, appKey }).exec();
		if (!action) {
			throw new Error(`Action with enum: ${actionEnum} not found for app with key: ${appKey}`);
		}

		return action;
	}
}
