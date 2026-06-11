<template>
  <div class="stat-chip glass-card">
    <div class="muted chip-label">{{ label }}</div>
    <div class="chip-value num" :class="tone">{{ value }}</div>
    <div v-if="sub" class="faint chip-sub">{{ sub }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  sub?: string
  tone?: 'up' | 'down' | ''
}>()
</script>

<style scoped>
.stat-chip {
  padding: 14px 18px;
  min-width: 130px;
}

.chip-label {
  font-size: 12px;
  margin-bottom: 6px;
}

.chip-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}

.chip-sub {
  font-size: 11px;
  margin-top: 4px;
}
</style>
