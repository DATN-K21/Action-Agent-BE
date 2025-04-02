import slugify from "slugify";

export class SlugifyHelper {
  static SLUGIFY_DEFAULT_OPTIONS = {
    trim: true,
    lower: true,
    strict: true,
    locale: "vi",
    replacement: "-",
  };
  static getDefaultOptions(): object {
    return SlugifyHelper.SLUGIFY_DEFAULT_OPTIONS;
  }

  static slugify(text: string, option: object = SlugifyHelper.SLUGIFY_DEFAULT_OPTIONS): string {
    return slugify(text, option);
  }
}