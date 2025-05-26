import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, HydratedDocument, Types } from 'mongoose';

export type AppDocument = HydratedDocument<App>;

@Schema({ timestamps: true, collection: 'Apps' })
export class App extends Document {    

  @Prop({
    default: () => new Types.ObjectId(),
    unique: true,
  })
  id: Types.ObjectId;

  @Prop({ required: true })
  key: string;

  @Prop({ required: true })
  name: string;

  @Prop({ default: '' })
  displayName: string;

  @Prop({ required: true })
  description: string;

  @Prop({ default: '' })
  logo: string;

  @Prop({ default: [] })
  categories: Array<string>;

  @Prop({ default: [] })
  tags: Array<string>;

  @Prop({ default: false })
  enabled: boolean;

  @Prop({ default: false })
  noAuth: boolean;

  @Prop({ default: false })
  isCustomApp: boolean;

  @Prop({ default: 0 })
  triggerCount: number;

  @Prop({ default: 0 })
  actionsCount: Number;

  @Prop({ default: [] })
  authSchemes: Array<Object>;

  @Prop({ default: '' })
  docs: string;

  @Prop({ default: '' })
  getCurrentUserEndpoint: string;

  @Prop({ default: [] })
  testConnectors: Array<{
    id: string;
    name: string;
    authScheme: string;
  }>;
}

export const AppSchema = SchemaFactory.createForClass(App);