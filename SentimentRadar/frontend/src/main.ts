import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
// ECharts 按需注册（控制包体）
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, ScatterChart } from 'echarts/charts'
import { GridComponent, MarkAreaComponent, MarkLineComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import App from './App.vue'
import router from './router'
import './styles/main.css'

use([CanvasRenderer, LineChart, ScatterChart, GridComponent, TooltipComponent, MarkLineComponent, MarkAreaComponent])

// 默认使用更明亮的玻璃主题，用户可在右上角切换并持久化。
const savedTheme = localStorage.getItem('radar-theme')
const initialTheme = savedTheme === 'dark' ? 'dark' : 'light'
document.documentElement.dataset.theme = initialTheme
document.documentElement.classList.toggle('dark', initialTheme === 'dark')

const app = createApp(App)
app.component('VChart', VChart)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
