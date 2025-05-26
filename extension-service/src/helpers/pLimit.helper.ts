// let pLimitInstance: typeof import('p-limit') | null = null;

// export async function getPLimit() {
//   if (!pLimitInstance) {
//     // Dynamically import p-limit (ESM compatible)
//     pLimitInstance = (await import('p-limit')).default;
//   }
//   return pLimitInstance;
// }

/////////////////////////////////////////////////////
import pLimit from 'p-limit';

export function getPLimit() {
  return pLimit;
}