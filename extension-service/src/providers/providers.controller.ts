import { Body, Controller, Delete, Get, Param, Patch, Post, Query } from '@nestjs/common';
import { ProvidersService } from '@/providers/providers.service';
import { IProviderPayload, IProviderQuery } from '@/providers/types/provider.types';
import { Provider } from '@/providers/provider.schema';
import { IResponse } from '@/types/response.type';

@Controller('providers')
export class ProvidersController {
  constructor(private readonly providerService: ProvidersService) { }

  @Get()
  async getProviders(@Query() query: IProviderQuery): Promise<IResponse<Provider[]>> {
    const { providers, meta } = await this.providerService.findAll(query);
    return {
      error_code: 0,
      message: 'Success',
      data: providers,
      meta: meta
    }
  }

  @Get(':id')
  async getProviderById(@Param('id') id: string): Promise<Provider> {
    return this.providerService.getDetailById(id);
  }

  @Get('slug/:slug')
  async getProviderBySlug(@Param('slug') slug: string): Promise<Provider> {
    return this.providerService.getDetailBySlug(slug);
  }

  @Get('name/:name')
  async getProviderByName(@Param('name') name: string): Promise<Provider> {
    return this.providerService.getDetailByName(name);
  }

  @Post()
  async createProvider(@Body() provider: IProviderPayload): Promise<Provider> {
    return this.providerService.create(provider);
  }

  @Patch(':id')
  async updateProvider(@Param('id') id: string, @Body() provider: IProviderPayload): Promise<Provider> {
    return this.providerService.update(id, provider);
  }

  @Delete(':id')
  async deleteProvider(@Param('id') id: string): Promise<string> {
    const deletedProvider = await this.providerService.delete(id);
    return deletedProvider.id;
  }
}
