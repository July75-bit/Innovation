/**
 * 白话导读：访问令牌（后端发的"身份凭证"）放在哪儿。
 *
 * 单独一个文件的原因：client.ts 要**读**它（每个请求都要带 Authorization 头），
 * useAuth.ts 要**写**它（登录/注册/退出）。如果放 useAuth 里就变成
 * api ↔ composables 循环导入，Vite 打包时会直接报错。
 *
 * 令牌本身的有效性由后端判断（GET /api/auth/me 或任何业务请求），
 * 这里只负责"存着、别丢、能取出来"。
 */

/** 存储键带版本号：令牌格式将来变了可以整体作废，不至于读到半截数据 */
const TOKEN_KEY = 'playerstock.auth.token.v1'

/** 内存里的那份 = 当前这一屏请求要用的；两个 Storage 里的份 = 刷新后能不能捞回来 */
let current: string | null = null

type Store = 'remember' | 'session'

function safeGet(store: Storage, key: string): string | null {
  try {
    return store.getItem(key)
  } catch {
    // 隐私模式 / 禁存储：当作没登录，不要让首屏崩在白屏上
    return null
  }
}

function safeSet(store: Storage, key: string, value: string | null): void {
  try {
    if (value === null) store.removeItem(key)
    else store.setItem(key, value)
  } catch {
    /* 存不下就算了：会话只在内存里，刷新掉线而已 */
  }
}

/**
 * 启动时恢复令牌：localStorage（勾了"记住我"）优先，其次 sessionStorage（本次标签页）。
 * 两边都清过才不会出现在一台共用电脑上"上次的人"还在登录着。
 */
export function restoreToken(): string | null {
  if (current !== null) return current
  current = safeGet(localStorage, TOKEN_KEY) ?? safeGet(sessionStorage, TOKEN_KEY)
  return current
}

export function getToken(): string | null {
  return current
}

/** 有令牌才算登录；remember=true 落 localStorage（关浏览器还在），否则只活于当前标签页 */
export function setToken(token: string, store: Store): void {
  current = token
  safeSet(localStorage, TOKEN_KEY, store === 'remember' ? token : null)
  safeSet(sessionStorage, TOKEN_KEY, store === 'session' ? token : null)
}

export function clearToken(): void {
  current = null
  safeSet(localStorage, TOKEN_KEY, null)
  safeSet(sessionStorage, TOKEN_KEY, null)
}
