<script setup lang="ts">
/**
 * 白话导读：注册 / 登录页（/auth），整页 CS2 背景，表单样式最重的一页，但逻辑很薄。
 *
 * 它自己不发任何请求，全部动作交给 composables/useAuth.ts（register/login/访客进入）。
 * 本页负责：登录/注册两个标签页切换、失焦逐字段校验、密码强度条、提交后跳去哪。
 *
 * 登录后跳哪：路由守卫把原本要去的地址放进 ?redirect=，这里读出来再跳过去；
 * 只接受以单个 / 开头的站内路径（防"开放重定向"，避免被利用跳转到外站）。
 */
/**
 * 注册 / 登录页（界面层）。
 *
 * 视觉：**纯色画布 + 实色表单面板**（内容层），全部色值走 tokens.css 语义令牌，
 * 因此浅色/深色双模式下都自动保证可读性；不再使用装饰背景图/渐变/玻璃/重阴影。
 * 窄屏（≤900px）单列堆叠，品牌区在上、表单在下。
 *
 * 行为：表单只调用 src/composables/useAuth.ts，界面不碰 fetch；
 * 第 7 轮之后那层已经改成真鉴权（令牌由后端签发），所以这一页现在**会**打后端。
 * 后端没起时提交会直接显示"无法连接后端服务"，不会假装登录成功。
 *
 * 注册字段按要求收敛到最小：用户名 + 密码（+ 确认密码）。
 */
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import {
  enterAsGuest,
  login,
  passwordStrength,
  register,
  validatePassword,
  validateUsername,
} from '../composables/useAuth'

type Tab = 'login' | 'register'

const route = useRoute()
const router = useRouter()

const tab = ref<Tab>(route.query.tab === 'register' ? 'register' : 'login')

/** 登录成功后去哪：守卫带进来的 ?redirect=，只接受站内相对路径（防开放重定向） */
const redirectTo = computed(() => {
  const raw = route.query.redirect
  const target = Array.isArray(raw) ? raw[0] : raw
  if (typeof target === 'string' && target.startsWith('/') && !target.startsWith('//')) {
    return target
  }
  return '/'
})

/* ---------- 表单状态 ---------- */
const loginForm = reactive({ username: '', password: '', remember: true })
const regForm = reactive({ username: '', password: '', confirm: '', remember: true })

/** 逐字段错误：失焦时校验，提交时再全量校验一遍 */
const loginErrors = reactive<Record<string, string | null>>({ username: null, password: null })
const regErrors = reactive<Record<string, string | null>>({
  username: null,
  password: null,
  confirm: null,
})

/**
 * 删除账号后 App.vue 会带 ?deleted=1 跳回这里。
 * 初始就把提示摆出来：用户刚做完一个不可逆操作，最不该看到的是"页面什么都没变"。
 */
const banner = reactive<{ kind: 'idle' | 'error' | 'ok'; text: string }>({
  kind: route.query.deleted === '1' ? 'ok' : 'idle',
  text:
    route.query.deleted === '1'
      ? '账号已删除，余额、持仓与流水已一并清除。可以重新注册一个，或用公共演示账户逛逛。'
      : '',
})
const pending = ref(false)
const showPassword = ref(false)

const strength = computed(() => passwordStrength(regForm.password))
const strengthClass = computed(() => `s${strength.value.score}`)

function switchTab(next: Tab): void {
  tab.value = next
  banner.kind = 'idle'
  banner.text = ''
}

/* ---------- 提交 ---------- */
async function submit(): Promise<void> {
  if (pending.value) return
  banner.kind = 'idle'
  banner.text = ''

  pending.value = true
  try {
    if (tab.value === 'login') {
      loginErrors.username = validateUsername(loginForm.username)
      loginErrors.password = loginForm.password ? null : '请填写密码'
      if (loginErrors.username || loginErrors.password) return

      const res = await login({ ...loginForm })
      if (!res.ok) {
        banner.kind = 'error'
        banner.text = res.message
        return
      }
      banner.kind = 'ok'
      banner.text = res.message
    } else {
      regErrors.username = validateUsername(regForm.username)
      regErrors.password = validatePassword(regForm.password)
      regErrors.confirm = regForm.confirm === regForm.password ? null : '两次输入的密码不一致'
      if (regErrors.username || regErrors.password || regErrors.confirm) return

      const res = await register({ ...regForm })
      if (!res.ok) {
        banner.kind = 'error'
        banner.text = res.message
        return
      }
      banner.kind = 'ok'
      banner.text = res.message
    }
    // 成功提示闪一下再跳转：立刻跳走的话，用户看不到"到底成功了没有"
    window.setTimeout(() => void router.replace(redirectTo.value), 450)
  } finally {
    pending.value = false
  }
}

/** 访客进入：后端没起 / 不想注册也能看界面 */
function asGuest(): void {
  enterAsGuest()
  void router.replace(redirectTo.value)
}
</script>

<template>
  <div class="auth-page">
    <div class="inner">
      <!-- ===== 左：品牌与说明 ===== -->
      <section class="pitch">
        <RouterLink to="/" class="brand">
          <span class="brand-mark" aria-hidden="true"></span>
          PlayerStock<span class="sub">虚拟选手股</span>
        </RouterLink>

        <h1>把喜欢的选手<br />当成一支支股票</h1>
        <p class="lede">CS2 职业选手的行情、持仓与交易流水，全程信用点，只为练手与展示。</p>

        <ul class="points">
          <li>
            <span class="dot" aria-hidden="true"></span>
            16 名选手行情与模拟表现分
          </li>
          <li>
            <span class="dot" aria-hidden="true"></span>
            买入 / 卖出即时结算，持仓与流水可回溯
          </li>
          <li>
            <span class="dot" aria-hidden="true"></span>
            注册即隔离账户：你的持仓与别人的互不可见
          </li>
        </ul>

        <p class="disclaimer">
          本项目为课程作品：全程信用点，不可充值 / 提现 / 兑换；选手信息与价格评分均为模拟数据，与
          Valve、HLTV 及相关俱乐部无关联，不构成投资建议。
        </p>
      </section>

      <!-- ===== 右：登录 / 注册面板 ===== -->
      <section class="panel" aria-labelledby="panel-title">
        <div class="tabs" role="tablist" aria-label="登录或注册">
          <button
            type="button"
            role="tab"
            :aria-selected="tab === 'login'"
            :class="['tab', { active: tab === 'login' }]"
            @click="switchTab('login')"
          >
            登录
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="tab === 'register'"
            :class="['tab', { active: tab === 'register' }]"
            @click="switchTab('register')"
          >
            注册
          </button>
        </div>

        <h2 id="panel-title">{{ tab === 'login' ? '欢迎回来' : '创建本地账号' }}</h2>
        <p class="hint">
          账号由后端签发访问令牌：注册后<strong>余额、持仓、流水各自独立</strong>，
          退出会真的撤销令牌（不是只删浏览器里的东西）。
        </p>

        <p
          v-if="banner.kind !== 'idle'"
          :class="['banner', banner.kind]"
          role="status"
          aria-live="polite"
        >
          {{ banner.text }}
        </p>

        <!-- ---------- 登录 ---------- -->
        <form v-if="tab === 'login'" class="form" novalidate @submit.prevent="submit">
          <label class="field" for="login-username">
            <span class="label">用户名</span>
            <input
              id="login-username"
              v-model="loginForm.username"
              name="username"
              type="text"
              autocomplete="username"
              placeholder="例如 s1mple 或 demo"
              :aria-invalid="Boolean(loginErrors.username)"
              :aria-describedby="loginErrors.username ? 'login-username-err' : undefined"
              @blur="loginErrors.username = validateUsername(loginForm.username)"
            />
          </label>
          <p v-if="loginErrors.username" id="login-username-err" class="err" role="alert">
            {{ loginErrors.username }}
          </p>

          <label class="field" for="login-password">
            <span class="label">密码</span>
            <div class="pw-wrap">
              <input
                id="login-password"
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                name="password"
                autocomplete="current-password"
                placeholder="••••••••"
                :aria-invalid="Boolean(loginErrors.password)"
                :aria-describedby="loginErrors.password ? 'login-password-err' : undefined"
                @blur="loginErrors.password = loginForm.password ? null : '请填写密码'"
              />
              <button type="button" class="pw-toggle" @click="showPassword = !showPassword">
                {{ showPassword ? '隐藏' : '显示' }}
              </button>
            </div>
          </label>
          <p v-if="loginErrors.password" id="login-password-err" class="err" role="alert">
            {{ loginErrors.password }}
          </p>

          <label class="check">
            <input v-model="loginForm.remember" type="checkbox" />
            <span>记住我（下次打开自动保持登录）</span>
          </label>

          <button class="submit" type="submit" :disabled="pending">
            {{ pending ? '登录中…' : '进入市场' }}
          </button>

          <p class="guest-note">
            不想注册？<button type="button" class="link-btn" @click="asGuest">先随便逛逛</button>
            —— 未登录时用的是公共演示账户，余额与持仓会和别的访客共享。
          </p>
          <p class="swap">
            还没有账号？
            <button type="button" class="link-btn" @click="switchTab('register')">立即注册</button>
          </p>
        </form>

        <!-- ---------- 注册：只要用户名 + 密码 ---------- -->
        <form v-else class="form" novalidate @submit.prevent="submit">
          <label class="field" for="reg-username">
            <span class="label">用户名</span>
            <input
              id="reg-username"
              v-model="regForm.username"
              name="username"
              type="text"
              autocomplete="username"
              placeholder="字母 / 数字 / 下划线，3–20 位"
              :aria-invalid="Boolean(regErrors.username)"
              :aria-describedby="regErrors.username ? 'reg-username-err' : undefined"
              @blur="regErrors.username = validateUsername(regForm.username)"
            />
          </label>
          <p v-if="regErrors.username" id="reg-username-err" class="err" role="alert">
            {{ regErrors.username }}
          </p>

          <label class="field" for="reg-password">
            <span class="label">密码</span>
            <div class="pw-wrap">
              <input
                id="reg-password"
                v-model="regForm.password"
                :type="showPassword ? 'text' : 'password'"
                name="new-password"
                autocomplete="new-password"
                placeholder="至少 8 位，含字母和数字"
                :aria-invalid="Boolean(regErrors.password)"
                :aria-describedby="regErrors.password ? 'reg-password-err' : 'pw-strength'"
                @blur="regErrors.password = validatePassword(regForm.password)"
              />
              <button type="button" class="pw-toggle" @click="showPassword = !showPassword">
                {{ showPassword ? '隐藏' : '显示' }}
              </button>
            </div>
          </label>
          <div id="pw-strength" class="strength" aria-hidden="true">
            <span :class="['bar', strengthClass]"><i></i><i></i><i></i></span>
            <span class="strength-text">{{
              strength.label ? `强度：${strength.label}` : ' '
            }}</span>
          </div>
          <p v-if="regErrors.password" id="reg-password-err" class="err" role="alert">
            {{ regErrors.password }}
          </p>

          <label class="field" for="reg-confirm">
            <span class="label">确认密码</span>
            <input
              id="reg-confirm"
              v-model="regForm.confirm"
              type="password"
              name="confirm_password"
              autocomplete="new-password"
              placeholder="再输入一次"
              :aria-invalid="Boolean(regErrors.confirm)"
              :aria-describedby="regErrors.confirm ? 'reg-confirm-err' : undefined"
              @blur="
                regErrors.confirm =
                  regForm.confirm === regForm.password ? null : '两次输入的密码不一致'
              "
            />
          </label>
          <p v-if="regErrors.confirm" id="reg-confirm-err" class="err" role="alert">
            {{ regErrors.confirm }}
          </p>

          <label class="check">
            <input v-model="regForm.remember" type="checkbox" />
            <span>记住我（下次打开自动保持登录）</span>
          </label>

          <button class="submit" type="submit" :disabled="pending">
            {{ pending ? '注册中…' : '注册并进入市场' }}
          </button>

          <p class="note">注册即表示了解：这是课程演示，信用点不可充值 / 提现 / 兑换。</p>

          <p class="swap">
            已经有账号了？
            <button type="button" class="link-btn" @click="switchTab('login')">去登录</button>
          </p>
        </form>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* 登录/注册页（内容层）：纯色画布 + 实色面板，浅/深两套令牌自动适配，无装饰图/渐变/玻璃/重阴影 */
.auth-page {
  position: relative;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
  background: var(--color-canvas);
}

.inner {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1180px;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(340px, 420px);
  gap: var(--space-6);
  align-items: center;
}

/* ===== 左侧品牌区 ===== */
.pitch {
  color: var(--text);
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: 800;
  font-size: var(--fs-h3);
  color: var(--text);
  text-decoration: none;
}
.brand .sub {
  font-weight: 400;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.brand-mark {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-action);
  border: 1px solid var(--color-action);
}
.pitch h1 {
  margin: var(--space-5) 0 var(--space-3);
  font-size: clamp(28px, 4.4vw, 44px);
  line-height: 1.18;
  letter-spacing: 0.5px;
  color: var(--text);
}
.lede {
  margin: 0;
  max-width: 42ch;
  font-size: var(--fs-h3);
  color: var(--muted);
}
.points {
  list-style: none;
  margin: var(--space-5) 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  font-size: var(--fs-body);
  color: var(--text);
}
.points li {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-action);
  flex-shrink: 0;
}
.disclaimer {
  margin: var(--space-5) 0 0;
  max-width: 52ch;
  font-size: var(--fs-cap);
  line-height: 1.6;
  color: var(--faint);
}

/* ===== 右侧面板：内容层（表单）→ 实色 + 1px 边框，不做玻璃 ===== */
.panel {
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}
.tabs {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  border-radius: var(--radius-sm);
  background: var(--neutral-bg);
}
.tab {
  display: inline-flex;
  align-items: center;
  min-height: 44px; /* 点击区 ≥44px */
  padding: 0 22px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-body);
  font-weight: 600;
  cursor: pointer;
}
.tab:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}
.tab.active {
  background: var(--color-action);
  color: var(--color-action-text);
}
.panel h2 {
  margin: var(--space-4) 0 4px;
  font-size: var(--fs-h2);
  color: var(--text);
}
.hint {
  margin: 0 0 var(--space-4);
  font-size: var(--fs-cap);
  line-height: 1.6;
  color: var(--muted);
}
.hint strong {
  color: var(--text);
  font-weight: 600;
}

.banner {
  margin: 0 0 var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--fs-aux);
}
.banner.error {
  background: var(--up-bg);
  color: var(--up-text);
}
.banner.ok {
  background: var(--down-bg);
  color: var(--down);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.label {
  font-size: var(--fs-aux);
  color: var(--muted);
}
.field input {
  width: 100%;
  min-height: 44px;
  padding: 10px var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-sunken);
  color: var(--text);
  font-size: var(--fs-body);
}
.field input::placeholder {
  color: var(--color-text-disabled);
}
.field input:hover:not(:disabled) {
  border-color: var(--color-border-strong);
}
.field input:focus {
  outline: 2px solid var(--color-focus);
  outline-offset: 0;
  border-color: var(--color-primary-500);
}
.field input[aria-invalid='true'] {
  border-color: var(--color-error-base);
}

.pw-wrap {
  position: relative;
  display: flex;
}
.pw-wrap input {
  padding-right: 56px;
}
.pw-toggle {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  min-height: 32px;
  padding: 4px 8px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--neutral-bg);
  color: var(--muted);
  font-size: var(--fs-cap);
  cursor: pointer;
}
.pw-toggle:hover {
  color: var(--text);
}
.pw-toggle:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.strength {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: -6px;
}
.bar {
  display: inline-flex;
  gap: 3px;
  flex: 1;
}
.bar i {
  height: 4px;
  flex: 1;
  border-radius: 2px;
  background: var(--neutral-bg);
}
.bar.s1 i:nth-child(1) {
  background: var(--color-error-base);
}
.bar.s2 i:nth-child(-n + 2) {
  background: var(--color-warning-base);
}
.bar.s3 i {
  background: var(--color-success-base);
}
.strength-text {
  font-size: var(--fs-cap);
  color: var(--muted);
  min-width: 44px;
  text-align: right;
}

.err {
  margin: -6px 0 0;
  font-size: var(--fs-cap);
  color: var(--color-error-base);
}

.check {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  font-size: var(--fs-aux);
  color: var(--muted);
  line-height: 1.5;
}
.check input {
  margin-top: 2px;
  accent-color: var(--color-primary-500);
  flex-shrink: 0;
}

.submit {
  margin-top: var(--space-1);
  min-height: 44px;
  padding: 11px var(--space-4);
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-action);
  color: var(--color-action-text);
  font-size: var(--fs-body);
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: pointer;
}
.submit:hover:not(:disabled) {
  background: var(--color-action-hover);
}
.submit:disabled {
  opacity: 0.6;
  cursor: progress;
}

.guest-note {
  margin: 0;
  font-size: var(--fs-cap);
  line-height: 1.6;
  color: var(--muted);
  text-align: center;
}
.note {
  margin: 0;
  font-size: var(--fs-cap);
  line-height: 1.5;
  color: var(--muted);
  text-align: center;
}
.swap {
  margin: 0;
  font-size: var(--fs-aux);
  color: var(--muted);
  text-align: center;
}
.link-btn {
  background: none;
  border: none;
  padding: 0;
  color: var(--accent-text);
  font-size: inherit;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.link-btn:hover {
  color: var(--text);
}

/* ===== ≤900px：单列堆叠，品牌区在上、表单占整行 ===== */
@media (max-width: 900px) {
  .auth-page {
    padding: var(--space-4);
  }
  .inner {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--space-5);
    max-width: 460px;
  }
  .pitch h1 {
    margin-top: var(--space-3);
    font-size: 26px;
  }
  .points {
    display: none;
  }
  .disclaimer {
    display: none;
  }
}
</style>
