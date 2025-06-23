import { Types } from 'mongoose';

export class MongooseHelper {
  static convertToObjectId(id: string): Types.ObjectId | undefined {
    if(Types.ObjectId.isValid(id)) {
      return new Types.ObjectId(id);
    }
    return undefined;
  }
}