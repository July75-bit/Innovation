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
 * 视觉：整页背景用处理过的 CS2 主视觉（压暗 + 轻微模糊 + 暗角，见 assets/auth-bg*.jpg），
 * 上面再叠一层渐变遮罩，保证表单文字在任何屏幕上都有足够对比度。
 * 窄屏（≤900px）换竖版裁切图，避免人物被横向挤扁、表单压成一条。
 *
 * 行为：表单只调用 src/composables/useAuth.ts，界面不碰 fetch；
 * 第 7 轮之后那层已经改成真鉴权（令牌由后端签发），所以这一页现在**会**打后端。
 * 后端没起时提交会直接显示"无法连接后端服务"，不会假装登录成功。
 *
 * 注册字段按要求收敛到最小：用户名 + 密码（+ 确认密码）。
 */
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import bgWide from '../assets/auth-bg.jpg'
import bgNarrow from '../assets/auth-bg-narrow.jpg'
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

/** 背景图交给 CSS 变量：scoped 样式里按屏幕宽度切换，JS 不参与布局判断 */
const bgVars = computed(() => ({
  '--bg-wide': `url(${bgWide})`,
  '--bg-narrow': `url(${bgNarrow})`,
}))

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
  <div class="auth-page" :style="bgVars">
    <!-- 遮罩层：左深右浅，把人物留在左侧、表单留在右侧可读区 -->
    <div class="veil" aria-hidden="true"></div>

    <div class="inner">
      <!-- ===== 左：品牌与说明 ===== -->
      <section class="pitch">
        <RouterLink to="/" class="brand">
          <span class="brand-mark" aria-hidden="true"></span>
          PlayerStock<span class="sub">虚拟选手股</span>
        </RouterLink>

        <h1>把喜欢的选手<br />当成一支支股票</h1>
        <p class="lede">CS2 职业选手的行情、持仓与交易流水，全程虚拟币，只为练手与展示。</p>

        <ul class="points">
          <li>
            <span class="dot" aria-hidden="true"></span>
            50 名选手行情与模拟表现分
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
          本项目为课程作品：全程虚拟币，不可充值 / 提现 / 兑换；选手信息与价格评分均为模拟数据，与
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

          <p class="note">注册即表示了解：这是课程演示，虚拟币不可充值 / 提现 / 兑换。</p>

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
.auth-page {
  position: relative;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
  /* 处理过的 CS2 主视觉：横向 cover 铺满，窄屏换竖版裁切 */
  background-image: var(--bg-wide);
  background-size: cover;
  background-position: center 38%;
  background-repeat: no-repeat;
  background-color: var(--bg);
}

/* 渐变遮罩：左侧压住人物高光、右侧给表单留可读区 */
.veil {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(
      100deg,
      rgba(8, 9, 11, 0.8) 0%,
      rgba(8, 9, 11, 0.52) 42%,
      rgba(8, 9, 11, 0.72) 100%
    ),
    radial-gradient(60% 55% at 78% 50%, rgba(229, 72, 77, 0.14), transparent 70%);
  pointer-events: none;
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
  background: var(--accent);
  box-shadow: 0 0 12px var(--accent);
}
.pitch h1 {
  margin: var(--space-5) 0 var(--space-3);
  font-size: clamp(28px, 4.4vw, 44px);
  line-height: 1.18;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 18px rgba(0, 0, 0, 0.65);
}
.lede {
  margin: 0;
  max-width: 42ch;
  font-size: var(--fs-h3);
  color: #d6d8dd;
  text-shadow: 0 1px 10px rgba(0, 0, 0, 0.6);
}
.points {
  list-style: none;
  margin: var(--space-5) 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  font-size: var(--fs-body);
  color: #dfe1e6;
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
  background: var(--accent);
  flex-shrink: 0;
}
.disclaimer {
  margin: var(--space-5) 0 0;
  max-width: 52ch;
  font-size: var(--fs-cap);
  line-height: 1.6;
  color: #a9adb6;
}

/* ===== 右侧面板 ===== */
.panel {
  padding: var(--space-5);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: var(--radius-lg);
  background: rgba(18, 20, 24, 0.78);
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow-2);
}
.tabs {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.07);
}
.tab {
  padding: 7px 22px;
  border: none;
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-body);
  font-weight: 600;
  cursor: pointer;
}
.tab.active {
  background: var(--accent);
  color: #fff;
  box-shadow: 0 2px 12px rgba(229, 72, 77, 0.45);
}
.panel h2 {
  margin: var(--space-4) 0 4px;
  font-size: var(--fs-h2);
}
.hint {
  margin: 0 0 var(--space-4);
  font-size: var(--fs-cap);
  line-height: 1.6;
  color: var(--muted);
}
.hint strong {
  color: #cfd2d8;
}

.banner {
  margin: 0 0 var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--fs-aux);
}
.banner.error {
  background: var(--up-bg);
  color: #ff8b8f;
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
  padding: 10px var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text);
  font-size: var(--fs-body);
}
.field input::placeholder {
  color: #6f727a;
}
.field input:focus {
  border-color: var(--accent);
  background: rgba(255, 255, 255, 0.06);
}
.field input[aria-invalid='true'] {
  border-color: var(--warn);
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
  padding: 4px 8px;
  border: none;
  border-radius: 6px;
  background: var(--neutral-bg);
  color: var(--muted);
  font-size: 11px;
  cursor: pointer;
}
.pw-toggle:hover {
  color: var(--text);
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
  background: rgba(255, 255, 255, 0.1);
}
.bar.s1 i:nth-child(1) {
  background: var(--warn);
}
.bar.s2 i:nth-child(-n + 2) {
  background: #d8c46a;
}
.bar.s3 i {
  background: var(--down);
}
.strength-text {
  font-size: 11px;
  color: var(--muted);
  min-width: 44px;
  text-align: right;
}

.err {
  margin: -6px 0 0;
  font-size: var(--fs-cap);
  color: var(--warn);
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
  accent-color: var(--accent);
  flex-shrink: 0;
}

.submit {
  margin-top: var(--space-1);
  padding: 11px var(--space-4);
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  font-size: var(--fs-body);
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(229, 72, 77, 0.35);
}
.submit:hover {
  filter: brightness(1.08);
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
  font-size: 11px;
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
  color: var(--accent);
  font-size: inherit;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.link-btn:hover {
  color: #ff6b70;
}

/* ===== ≤900px：品牌区收到上面、表单占整行，背景换竖版 ===== */
@media (max-width: 900px) {
  .auth-page {
    background-image: var(--bg-narrow);
    background-position: center top;
    padding: var(--space-4);
  }
  .veil {
    background: linear-gradient(
      180deg,
      rgba(8, 9, 11, 0.82) 0%,
      rgba(8, 9, 11, 0.72) 55%,
      rgba(8, 9, 11, 0.9) 100%
    );
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
