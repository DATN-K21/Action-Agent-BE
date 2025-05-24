import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, HydratedDocument } from 'mongoose';

export type ActionDocument = HydratedDocument<Action>;

@Schema({ timestamps: true, collection: 'Actions' })
export class Action extends Document {
  @Prop({ required: true, ref: 'App' })
  appKey: string;

  @Prop({ required: true, unique: true })
  enum: string;

  @Prop({ required: true, unique: true })
  name: string;

  @Prop({ default: '' })
  displayName: string;

  @Prop({ default: '' })
  description: string;

  @Prop({ default: '' })
  logo: string;

  @Prop({ default: [] })
  tags: Array<string>;

	@Prop({ default: false })
	deprecated: boolean;

  @Prop({ default: '' })
  version: string;

  @Prop({ default: [] })
  availableVersions: Array<string>;

  @Prop({ default: false })
  noAuth: boolean;
}

export const ActionSchema = SchemaFactory.createForClass(Action);