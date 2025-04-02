export type IProviderPayload = {
  name: string;
  url: string;
  slug?: string;
  description?: string;
  image_url?: string;
}

export type IProviderQuery = {
  page: number;
  limit: number;
}