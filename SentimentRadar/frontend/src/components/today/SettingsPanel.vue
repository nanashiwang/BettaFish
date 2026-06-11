<template>
  <div v-if="loading" v-loading="true" class="loading-block" />
  <el-row v-else :gutter="16">
    <el-col :xs="24" :md="14">
      <div class="glass-card panel">
        <h3 class="section-title">我的关注</h3>
        <p class="muted intro">添加关注的股票、主题或板块，当日话题命中时会在「我的关注」中提示。</p>
        <div v-for="group in GROUPS" :key="group.type" class="group">
          <div class="group-label muted">{{ group.label }}</div>
          <div class="group-tags">
            <el-tag
              v-for="item in itemsOf(group.type)"
              :key="item.id"
              closable
              effect="plain"
              @close="handleRemove(item.id)"
            >
              {{ item.name }}
            </el-tag>
            <el-input
              v-if="editingType === group.type"
              ref="inputRef"
              v-model="inputValue"
              size="small"
              class="tag-input"
              :placeholder="`回车添加${group.label}`"
              @keyup.enter="handleAdd(group.type)"
              @blur="editingType = ''"
            />
            <el-button v-else size="small" text type="primary" @click="startEditing(group.type)">
              + 添加
            </el-button>
          </div>
        </div>
      </div>
    </el-col>

    <el-col :xs="24" :md="10">
      <div class="glass-card panel coming-soon">
        <h3 class="section-title">推送提醒</h3>
        <div v-for="template in pushTemplates" :key="template.id" class="template-row">
          <div>
            <div>{{ template.name }}</div>
            <div class="faint">{{ template.time }}</div>
          </div>
          <el-switch :model-value="false" disabled />
        </div>
        <p class="faint hint">推送能力即将上线，先把关注列表建好</p>
      </div>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { addWatchItem, fetchSettings, removeWatchItem } from '../../api/radar'
import type { RadarSettings, WatchItem } from '../../api/types'

const GROUPS = [
  { type: 'stock', label: '股票' },
  { type: 'theme', label: '主题' },
  { type: 'sector', label: '板块' },
]

const loading = ref(true)
const items = ref<WatchItem[]>([])
const pushTemplates = ref<RadarSettings['push_templates']>([])
const editingType = ref('')
const inputValue = ref('')
const inputRef = ref()

function itemsOf(type: string) {
  return items.value.filter((item) => item.type === type)
}

function startEditing(type: string) {
  editingType.value = type
  inputValue.value = ''
  nextTick(() => inputRef.value?.[0]?.focus?.())
}

async function handleAdd(type: string) {
  const name = inputValue.value.trim()
  if (!name) return
  const result = await addWatchItem(type, name)
  items.value = result.items
  inputValue.value = ''
  ElMessage.success('已添加关注')
}

async function handleRemove(itemId: number) {
  const result = await removeWatchItem(itemId)
  items.value = result.items
}

onMounted(async () => {
  try {
    const result = await fetchSettings()
    items.value = result.settings.watchlist
    pushTemplates.value = result.settings.push_templates
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.loading-block {
  height: 240px;
}

.panel {
  padding: 20px 22px;
  margin-bottom: 16px;
}

.intro {
  margin: -6px 0 14px;
}

.group {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.group:last-child {
  border-bottom: none;
}

.group-label {
  width: 36px;
  flex-shrink: 0;
  padding-top: 4px;
}

.group-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-input {
  width: 140px;
}

.coming-soon {
  opacity: 0.85;
}

.template-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 14px;
}

.hint {
  margin: 14px 0 0;
  font-size: 12px;
}
</style>
