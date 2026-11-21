<script setup lang="ts">
/**
 * 404 页：拼错/过期链接的落点。
 *
 * 以前兜底是"悄悄重定向回市场"——用户以为地址是对的，其实看到的是另一页。
 * 现在明确告知"这个页面不存在"，并给一条回市场的路；同时保留 public（未登录也能看到）。
 */
import { RouterLink } from 'vue-router'
</script>

<template>
  <section class="nf">
    <p class="nf-code" aria-hidden="true">404</p>
    <h1>这个页面不存在</h1>
    <p class="nf-text">链接可能过期了，或者地址里打错了一个字。</p>
    <RouterLink class="nf-home" to="/">回到市场</RouterLink>
  </section>
</template>

<style scoped>
.nf {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: var(--space-3);
  max-width: 44ch;
}
.nf-code {
  margin: 0;
  font-size: 96px;
  font-weight: 600;
  line-height: 1;
  letter-spacing: -0.04em;
  color: var(--color-border-strong);
}
.nf h1 {
  margin: 0;
  font-size: var(--fs-h1);
  font-weight: 600;
}
.nf-text {
  margin: 0;
  color: var(--muted);
  font-size: var(--fs-body);
}
.nf-home {
  margin-top: var(--space-3);
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 0 var(--space-5);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  color: var(--text);
  font-size: var(--fs-aux);
  text-decoration: none;
  transition:
    background-color var(--motion-fast) ease,
    border-color var(--motion-fast) ease;
}
.nf-home:hover {
  background: var(--neutral-bg);
  border-color: var(--color-text-faint);
}
</style>
