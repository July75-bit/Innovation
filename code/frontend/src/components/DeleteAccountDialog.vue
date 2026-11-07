<script setup lang="ts">
/**
 * 白话导读：删除账号的确认弹窗。
 *
 * 为什么这么麻烦（口令 + 手输用户名两道确认）：删的是余额、持仓、流水，**不可恢复**。
 * 只靠"点一个红色按钮"就删号，在共用电脑 / 手滑的场景下是不可接受的失败模式，
 * 所以后端也坚持要口令（契约 §4.16），前端只是把这道闸做得更难误触。
 *
 * 请求由本组件发（与 TradePanel 直接调 api 的既有风格一致）：
 * 父层只管"开 / 关 / 删完去哪儿"，不掺和确认逻辑。
 */
import { computed, nextTick, ref, watch } from 'vue'

import { useAuth } from '../composables/useAuth'

const props = defineProps<{ nickname: string }>()

const { deleteAccount } = useAuth()

const open = defineModel<boolean>({ required: true })
const emit = defineEmits<{ deleted: [message: string] }>()

const password = ref('')
const confirmName = ref('')
const pending = ref(false)
const error = ref('')

/** 两道确认都过了才允许按删除：手滑打错用户名也删不掉 */
const ready = computed(
  () =>
    password.value.length > 0 &&
    confirmName.value.trim().toLowerCase() === props.nickname.toLowerCase(),
)

const passwordInput = ref<HTMLInputElement | null>(null)

watch(open, async (value) => {
  if (!value) return
  password.value = ''
  confirmName.value = ''
  error.value = ''
  pending.value = false
  await nextTick()
  passwordInput.value?.focus()
})

/** ESC 关掉：确认类弹窗必须能一键退出，否则键盘用户被卡在原地 */
function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && open.value) open.value = false
}

async function submit(): Promise<void> {
  if (!ready.value || pending.value) return
  pending.value = true
  error.value = ''
  try {
    const res = await deleteAccount(password.value)
    if (res.ok) {
      // 顺序要紧：先通知父层（它负责跳转），再关自己。
      // 反过来写会踩坑——父层收到事件时组件可能已经因为会话清空而被卸载
      emit('deleted', res.message)
      open.value = false
    } else {
      error.value = res.message
    }
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="mask" @keydown="onKeydown" @click.self="open = false">
      <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="del-title" tabindex="-1">
        <h3 id="del-title">删除账号 {{ nickname }}</h3>
        <p class="warn">
          不可恢复：余额、持仓、交易流水会一并删除，用户名将被释放。 公共演示账户不受影响。
        </p>

        <label class="field" for="del-password">
          <span class="label">请输入当前密码</span>
          <input
            id="del-password"
            ref="passwordInput"
            v-model="password"
            type="password"
            autocomplete="current-password"
            placeholder="后端会再校验一次"
          />
        </label>

        <label class="field" for="del-name">
          <span class="label"
            >请输入用户名
            <code>{{ nickname }}</code>
            以确认</span
          >
          <input
            id="del-name"
            v-model="confirmName"
            type="text"
            autocomplete="off"
            spellcheck="false"
            :placeholder="nickname"
          />
        </label>

        <p v-if="error" class="err" role="alert">{{ error }}</p>

        <div class="actions">
          <button type="button" class="cancel" @click="open = false">取消</button>
          <button
            type="button"
            class="danger"
            :disabled="!ready || pending"
            :title="ready ? '确认删除' : '需要先填密码并手输用户名'"
            @click="submit"
          >
            {{ pending ? '删除中…' : '永久删除账号' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(2px);
}
.dialog {
  width: min(420px, 100%);
  padding: var(--space-5);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-2);
  outline: none;
}
.dialog h3 {
  margin: 0 0 var(--space-2);
  font-size: var(--fs-h2);
}
.warn {
  margin: 0 0 var(--space-4);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  background: var(--warn-bg);
  color: var(--warn);
  font-size: var(--fs-aux);
  line-height: 1.5;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: var(--space-3);
}
.label {
  font-size: var(--fs-aux);
  color: var(--muted);
}
.label code {
  padding: 0 5px;
  border-radius: 4px;
  background: var(--neutral-bg);
  color: var(--text);
  font-size: 12px;
}
.field input {
  width: 100%;
  padding: 10px var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  color: var(--text);
  font-size: var(--fs-body);
}
.field input:focus {
  border-color: var(--accent);
}
.err {
  margin: 0 0 var(--space-3);
  font-size: var(--fs-cap);
  color: var(--warn);
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  margin-top: var(--space-4);
}
.cancel {
  padding: 9px var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: none;
  color: var(--muted);
  font-size: var(--fs-body);
  cursor: pointer;
}
.cancel:hover {
  color: var(--text);
}
.danger {
  padding: 9px var(--space-4);
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  font-size: var(--fs-body);
  font-weight: 700;
  cursor: pointer;
}
.danger:disabled {
  /* 没填全就压暗而不是隐藏：让人看得见"还差什么"，而不是找不到按钮 */
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
