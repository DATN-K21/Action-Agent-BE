// let pLimitInstance: typeof import('p-limit') | null = null;

// export async function getPLimit() {
//   if (!pLimitInstance) {
//     // Dynamically import p-limit (ESM compatible)
//     pLimitInstance = (await import('p-limit')).default;
//   }
//   return pLimitInstance;
// }

/////////////////////////////////////////////////////

type PLimit = typeof import('p-limit')['default'];

let pLimitInstance: PLimit | null = null;

export async function getPLimit() {
  if (!pLimitInstance) {
    // Dynamically import p-limit (ESM compatible)
    pLimitInstance = (await import('p-limit')).default;
  }
  return pLimitInstance;
}