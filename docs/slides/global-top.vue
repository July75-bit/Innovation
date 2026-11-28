<!-- 用 global-top 而不是 global-bottom：导出时 bottom 层画在幻灯片底下，会被纸色背景盖住。每页右下角的页码与页脚小字（封面和最后一页不显示），像印刷品的页眉页脚 -->
<template>
  <footer
    v-if="$nav.currentPage > 1 && $nav.currentPage < $nav.total"
    class="deck-folio"
  >
    <span>PlayerStock · 结课项目审查</span>
    <span class="deck-folio-num">{{ String($nav.currentPage).padStart(2, '0') }} / {{ $nav.total }}</span>
  </footer>
</template>
