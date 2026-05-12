import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from '@/router'
import App from './App.vue'
import './styles/global.css'
import './styles/fonts.css'
import './styles/tailwind.css'
// 确保 request 模块被加载（注册全局拦截器）
import '@/utils/request'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
