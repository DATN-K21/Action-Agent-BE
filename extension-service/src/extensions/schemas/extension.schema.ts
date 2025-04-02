import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Types, HydratedDocument } from 'mongoose';

export type ExtensionDocument = HydratedDocument<Extension>;

@Schema({ timestamps: true, collection: 'Extensions' })
export class Extension extends Document {
  @Prop({ required: true, unique: true })
  key: string;

  @Prop({ required: true, unique: true })
  name: string;

  @Prop({ default: '' })
  description: string;

  @Prop({ required: true, ref: 'Provider' })
  provider_id: string;

  @Prop({ default: 0 })
  total_tools: number;

  @Prop({ type: [
    { type: Types.ObjectId, ref: 'Category' }
  ]})
  category_ids: Types.ObjectId[];
}

export const ExtensionSchema = SchemaFactory.createForClass(Extension);

// Add a virtual field to populate extensions
ExtensionSchema.virtual('tools', {
  ref: 'Tool',
  localField: '_id',
  foreignField: 'extension_id',
});
