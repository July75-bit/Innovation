/**
 * GET 响应小缓存：页面来回切、快速点开再返回时，不再重复等同一份数据。
 *
 * 设计取舍：
 * - 只缓存 GET（只读、幂等），POST（交易/登录/决策）永不缓存；
 * - 带 TTL（默认见 api/index.ts），交易成功或点"刷新"时整体失效；
 * - **并发合并**：同一个 key 在飞行中只发一次请求（详情页三个接口/双挂载不会重复打）；
 * - 失败不缓存，避免把一次网络抖动记成 60 秒的空白。
 *
 * 不做持久化（localStorage）：数据时效性比"快"更重要，内存缓存已经能解决"来回切"的场景。
 */
interface Entry {
  value: unknown
  expiresAt: number
}

const values = new Map<string, Entry>()
const inflight = new Map<string, Promise<unknown>>()

/** 读缓存；没有/过期就执行 loader，并合并同一时刻的并发请求 */
export function cached<T>(key: string, ttlMs: number, loader: () => Promise<T>): Promise<T> {
  const hit = values.get(key)
  if (hit && hit.expiresAt > Date.now()) return Promise.resolve(hit.value as T)

  const running = inflight.get(key)
  if (running) return running as Promise<T>

  const task = loader()
    .then((value) => {
      values.set(key, { value, expiresAt: Date.now() + ttlMs })
      return value
    })
    .finally(() => {
      inflight.delete(key)
    })
  inflight.set(key, task)
  return task
}

/** 失效：给前缀就只清这一类（如 `player:` / `analysis:`），不给就整体清空 */
export function invalidateCache(prefix?: string): void {
  for (const key of values.keys()) {
    if (!prefix || key.startsWith(prefix)) values.delete(key)
  }
}

/** 仅测试/调试用 */
export function __cacheSize(): number {
  return values.size
}
