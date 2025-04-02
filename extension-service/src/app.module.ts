import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ProvidersModule } from './providers/providers.module';
import { ExtensionsModule } from './extensions/extensions.module';

@Module({
  imports: [ProvidersModule, ExtensionsModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
