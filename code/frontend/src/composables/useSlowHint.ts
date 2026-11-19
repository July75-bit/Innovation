/**
 * 慢加载提示：数据请求超过 N 秒还没回来时，给一句"可能在唤醒服务"的解释。
 *
 * 背景：Render 免费后端闲置 15 分钟会休眠，冷启动约 30 秒；这期间页面只有转圈/骨架，
 * 用户不知道是在等什么。超过 4 秒就把原因与预期时间说出来，比"一直转圈像卡死"体验好。
 */
import { onBeforeUnmount, ref, watch, type Ref } from 'vue'

export function useSlowHint(active: Ref<boolean>, delayMs = 4000) {
  const slow = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null

  const clear = () => {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  watch(
    active,
    (on) => {
      clear()
      slow.value = false
      if (!on) return
      timer = setTimeout(() => {
        slow.value = true
      }, delayMs)
    },
    { immediate: true },
  )
  onBeforeUnmount(clear)

  return slow
}
