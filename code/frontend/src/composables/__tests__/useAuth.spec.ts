/**
 * 本地账号态的回归测试。
 *
 * 注册 / 登录的界面（AuthView）只是这层的壳，逻辑全部放在 useAuth 里测最省劲：
 * 校验规则、重复用户名、密码摘要不落明文、"记住我"落在哪个 Storage、访客态能不能放行。
 *
 * 注册字段按要求收敛成"用户名 + 密码"，所以这里也没有昵称/邮箱的用例了。
 *
 * 注意：账号表是模块级状态，同一个测试文件里用例之间会互相看得见，
 * 所以每条用例都用自己独占的用户名，别指望 beforeEach 能把内存里的表清空。
 */
import { beforeEach, describe, expect, it } from 'vitest'

import {
  DEMO_PASSWORD,
  DEMO_USERNAME,
  enterAsGuest,
  ensureDemoUser,
  login,
  logout,
  passwordStrength,
  register,
  useAuth,
  validatePassword,
  validateUsername,
} from '../useAuth'

/** 与 useAuth 内部同名：测试里直接写死，是为了验证"记住我"到底写进哪个 Storage */
const USERS_KEY = 'playerstock.auth.users.v1'
const SESSION_KEY = 'playerstock.auth.session.v1'
const SESSION_ONCE_KEY = 'playerstock.auth.session.v1.once'

const { session, currentUser, isAuthenticated, isLoggedIn, isGuest, registeredCount } = useAuth()

/** 注册只填用户名 + 密码，其余参数在测试里保持默认 */
const reg = (username: string, password = 'abcd1234', remember = true) =>
  register({ username, password, confirm: password, remember })

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  logout()
})

describe('表单校验', () => {
  it('用户名：空 / 太短 / 非法字符都要拦，正常值放行', () => {
    expect(validateUsername('')).toMatch(/请填写/)
    expect(validateUsername('ab')).toMatch(/至少 3/)
    expect(validateUsername('s1 mple')).toMatch(/字母、数字和下划线/)
    expect(validateUsername('s1mple')).toBeNull()
  })

  it('密码：长度与字母+数字两条规则', () => {
    expect(validatePassword('a1')).toMatch(/至少 8/)
    expect(validatePassword('allletters')).toMatch(/字母和数字/)
    expect(validatePassword('demo1234')).toBeNull()
  })

  it('强度条只提示不拦截：纯字母数字=中，带符号或更长=较强', () => {
    expect(passwordStrength('demo1234').score).toBe(2)
    expect(passwordStrength('demo1234!').score).toBe(3)
    expect(passwordStrength('').score).toBe(0)
  })
})

describe('注册', () => {
  it('用户名 + 密码就能写号，成功后即登录，且密码不落明文', async () => {
    const res = await reg('zhangsan')

    expect(res.ok).toBe(true)
    expect(currentUser.value?.username).toBe('zhangsan')
    expect(isLoggedIn.value).toBe(true)
    expect(localStorage.getItem(USERS_KEY)).not.toContain('abcd1234')
  })

  it('两次密码不一致时不写号', async () => {
    const before = registeredCount.value

    const res = await register({
      username: 'lisi',
      password: 'abcd1234',
      confirm: 'abcd1235',
      remember: true,
    })

    expect(res.ok).toBe(false)
    expect(res.message).toMatch(/不一致/)
    expect(registeredCount.value).toBe(before)
    expect(session.value).toBeNull()
  })

  it('重名（忽略大小写）直接拒绝，避免两个账号互相顶掉', async () => {
    await reg('wangwu')

    const dup = await reg('WangWu')

    expect(dup.ok).toBe(false)
    expect(dup.message).toMatch(/已存在/)
  })

  it('太弱的密码进不去', async () => {
    const before = registeredCount.value

    const res = await reg('weak_user', 'short1')

    expect(res.ok).toBe(false)
    expect(res.message).toMatch(/至少 8/)
    expect(registeredCount.value).toBe(before)
  })
})

describe('登录', () => {
  it('密码不对不进；对了才建会话', async () => {
    await reg('zhaoliu')
    logout()

    const bad = await login({ username: 'zhaoliu', password: 'wrong123', remember: true })
    expect(bad.ok).toBe(false)
    expect(bad.message).toMatch(/密码不正确/)
    expect(isAuthenticated.value).toBe(false)

    const good = await login({ username: 'zhaoliu', password: 'abcd1234', remember: true })
    expect(good.ok).toBe(true)
    expect(currentUser.value?.username).toBe('zhaoliu')
  })

  it('账号不存在时提示去注册，而不是含糊报"密码错误"', async () => {
    const res = await login({ username: 'nobody_here', password: 'abcd1234', remember: true })

    expect(res.ok).toBe(false)
    expect(res.message).toMatch(/注册/)
  })

  it('记住我=true 落 localStorage，=false 只活于当前标签页', async () => {
    await reg('qianqi', 'abcd1234', false)
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
    expect(sessionStorage.getItem(SESSION_ONCE_KEY)).not.toBeNull()

    await login({ username: 'qianqi', password: 'abcd1234', remember: true })
    expect(localStorage.getItem(SESSION_KEY)).not.toBeNull()
    // 换回"不记住"时要清掉上次的长期会话，否则关掉浏览器还能混进去
    await login({ username: 'qianqi', password: 'abcd1234', remember: false })
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })
})

describe('访客与退出', () => {
  it('访客态算"可以逛"，但不算登录', () => {
    enterAsGuest()

    expect(isGuest.value).toBe(true)
    expect(isAuthenticated.value).toBe(true)
    expect(isLoggedIn.value).toBe(false)
    expect(currentUser.value).toBeNull()
    // 访客不该在下次打开时还占着登录位
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('退出把两个 Storage 的会话都清干净', async () => {
    await reg('sunba')
    expect(localStorage.getItem(SESSION_KEY)).not.toBeNull()

    logout()

    expect(session.value).toBeNull()
    expect(isAuthenticated.value).toBe(false)
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
    expect(sessionStorage.getItem(SESSION_ONCE_KEY)).toBeNull()
  })
})

describe('演示账号', () => {
  it('ensureDemoUser 幂等：重复调用后 demo 仍能正常登录', async () => {
    await ensureDemoUser()
    await ensureDemoUser()

    const res = await login({ username: DEMO_USERNAME, password: DEMO_PASSWORD, remember: true })
    expect(res.ok).toBe(true)
    expect(currentUser.value?.username).toBe(DEMO_USERNAME)

    const wrong = await login({ username: DEMO_USERNAME, password: 'nope1234', remember: true })
    expect(wrong.ok).toBe(false)
  })
})
