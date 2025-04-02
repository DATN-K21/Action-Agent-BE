import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, HydratedDocument } from 'mongoose';

export type GenreDocument = HydratedDocument<Provider>;

@Schema({ timestamps: true, collection: 'Providers' })
export class Provider extends Document {
  @Prop({ required: true, unique: true })
  slug: string;

  @Prop({ required: true, unique: true })
  name: string;

  @Prop({ required: true })
  url: string;

  @Prop({ default: '' })
  description: string;

  
  @Prop({ default: '' })
  image_url: string;
}

export const ProviderSchema = SchemaFactory.createForClass(Provider);

// Add a virtual field to populate extensions
ProviderSchema.virtual('extensions', {
  ref: 'Extension',
  localField: '_id',
  foreignField: 'providerId',
});
