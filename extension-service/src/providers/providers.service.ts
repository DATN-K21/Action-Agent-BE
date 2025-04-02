import { BadRequestException, ConflictException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Provider } from '@/providers/provider.schema';
import { Model } from 'mongoose';
import { IProviderPayload, IProviderQuery } from '@/providers/types/provider.types';
import { SlugifyHelper } from '@/helpers/slugify.helper';
import { MongooseHelper } from '@/helpers/mongoose.helper';
import { IQueryMeta } from '@/types/response.type';

@Injectable()
export class ProvidersService {
  constructor(
    @InjectModel(Provider.name) private readonly providerModel: Model<Provider>,
  ) { }

  async create(provider: IProviderPayload): Promise<Provider> {
    if (!provider?.slug) {
      provider.slug = SlugifyHelper.slugify(provider.name);
    }

    const existingProvider = await this.providerModel.findOne({
      $or: [
        { name: provider.name },
        { slug: provider.slug },
      ]
    });
    if (existingProvider) {
      throw new ConflictException(`Provider with name ${provider.name} or slug ${provider.slug} already exists`);
    }

    const createdProvider = this.providerModel.create(provider);
    return createdProvider;
  }

  async findAll(query: IProviderQuery): Promise<{ providers: Provider[], meta: IQueryMeta }> { 
    const { page, limit } = query;
    const skip = (page - 1) * limit;

    const totalItems = await this.providerModel.countDocuments().exec();

    const providers: Provider[] = await this.providerModel.find().skip(skip).limit(limit).exec();
    const meta: IQueryMeta = {
      page: page,
      per_page: limit,
      total_pages: Math.ceil(totalItems / limit),
      items: providers.length,
      total_items: totalItems,
    }
    return { providers, meta };
  }

  async getDetailById(id: string): Promise<Provider> {  
    const foundProvider = await this.providerModel.findById(MongooseHelper.convertToObjectId(id)).populate('extensions');
    if (!foundProvider) {
      throw new NotFoundException(`Provider with id ${id} not found`);
    }
    return foundProvider;
  }

  async getDetailBySlug(slug: string): Promise<Provider> {
    const foundProvider = await this.providerModel.findOne({ slug }).populate('extensions');
    if (!foundProvider) {
      throw new NotFoundException(`Provider with slug ${slug} not found`);
    }
    return foundProvider;
  }

  async getDetailByName(name: string): Promise<Provider> {
    const foundProvider = await this.providerModel.findOne({ name }).populate('extensions');
    if (!foundProvider) {
      throw new NotFoundException(`Provider with name ${name} not found`);
    }
    return foundProvider;    
  }

  async update(id: string, provider: IProviderPayload): Promise<Provider> { 
    const foundProvider = await this.providerModel.findById(MongooseHelper.convertToObjectId(id));
    if (!foundProvider) {
      throw new NotFoundException(`Provider with id ${id} not found`);
    }

    const updatedProvider = await this.providerModel.findByIdAndUpdate(
      MongooseHelper.convertToObjectId(id),
      { $set: provider },
      { new: true, raw: true },
    );
    if (!updatedProvider) {
      throw new BadRequestException(`Failed to update provider with id ${id}`);
    }

    return updatedProvider;
  }

  async delete(id: string): Promise<Provider> {
    const foundProvider = await this.providerModel.findById(MongooseHelper.convertToObjectId(id));
    if (!foundProvider) {
      throw new NotFoundException(`Provider with id ${id} not found`);
    }

    const deletedProvider = await this.providerModel.findByIdAndDelete(MongooseHelper.convertToObjectId(id));
    if (!deletedProvider) {
      throw new BadRequestException(`Failed to delete provider with id ${id}`);
    }

    return deletedProvider;
  }
}
