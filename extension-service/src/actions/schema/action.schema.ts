import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, HydratedDocument, Types } from 'mongoose';

export type ActionDocument = HydratedDocument<Action>;

@Schema({ timestamps: true, collection: 'Actions' })
export class Action extends Document {
  @Prop({
      default: () => new Types.ObjectId(),
      unique: true,
    })
    id: Types.ObjectId;

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

  @Prop({ type: Object, default: {} })
  parameters: {
    properties?: Record<string, any>;
    required?: string[];
    title?: string;
    type?: string;
  };

  @Prop({ type: Object, default: {} })
  responses: {
    properties?: Record<string, any>;
    required?: string[];
    title?: string;
    type?: string;
  }
}

export const ActionSchema = SchemaFactory.createForClass(Action);