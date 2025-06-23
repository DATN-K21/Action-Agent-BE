export type IResponse<T> = {
  error_code: number;
  message: string;
  data: T;
  meta: any;
}

export type IQueryMeta = {
  page: number;
  per_page: number;
  total_pages: number;
  items: number;
  total_items: number;
}