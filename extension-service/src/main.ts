import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { EnvironmentConfig } from './configs/environment.config';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  await app.listen(EnvironmentConfig.PORT ?? 3000);
  console.log(`Application is running on: ${await app.getUrl()}`);
}
bootstrap();
