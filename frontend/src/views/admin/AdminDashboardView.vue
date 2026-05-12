<script setup lang="ts">
import { onMounted, computed, ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  Users,
  CalendarDays,
  UserCheck,
  Clock,
  Building2,
  TrendingUp,
  AlertCircle,
  ArrowRight,
} from 'lucide-vue-next'
import AdminSidebar from '@/components/layout/AdminSidebar.vue'
import { useDashboard } from '@/composables/useDashboard'
import { useCountUp } from '@/composables/useCountUp'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const router = useRouter()
const { data, loading, error, fetchDashboard, retry } = useDashboard()

// 折线图 canvas ref & 实例
const trendCanvas = ref<HTMLCanvasElement | null>(null)
let trendChart: Chart | null = null

function renderTrendChart() {
  if (!data.value?.trend?.length || !trendCanvas.value) return

  if (trendChart) {
    trendChart.destroy()
  }

  const labels = data.value.trend.map((t) => {
    const parts = t.date.split('-')
    return `${parts[1]}/${parts[2]}`
  })

  trendChart = new Chart(trendCanvas.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: '参与人次',
          data: data.value.trend.map((t) => t.new_participations),
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.3,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#10B981',
          pointBorderColor: '#fff',
          pointBorderWidth: 1.5,
          borderWidth: 2,
        },
        {
          label: '新增活动',
          data: data.value.trend.map((t) => t.new_activities),
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.05)',
          fill: true,
          tension: 0.3,
          borderDash: [6, 3],
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#3B82F6',
          pointBorderColor: '#fff',
          pointBorderWidth: 1.5,
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index',
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: 'rgba(255,255,255,0.96)',
          titleColor: '#1E293B',
          bodyColor: '#64748B',
          borderColor: 'rgba(0,0,0,0.06)',
          borderWidth: 1,
          padding: 10,
          boxPadding: 4,
          titleFont: { size: 13, weight: '600' },
          bodyFont: { size: 12 },
          cornerRadius: 8,
          displayColors: true,
          callbacks: {
            title(items) {
              if (items.length) return items[0].label.replace('/', '月') + '日'
              return ''
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#94A3B8', font: { size: 11 } },
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: {
            color: '#94A3B8',
            font: { size: 11 },
            stepSize: 1,
          },
        },
      },
    },
  })
}

watch(() => data.value?.trend, async () => {
  await nextTick()
  renderTrendChart()
})

// 统计数字递增动画
const { count: totalUsersCount } = useCountUp(computed(() => data.value?.total_users ?? 0), 600)
const { count: totalActivitiesCount } = useCountUp(computed(() => data.value?.total_activities ?? 0), 600)
const { count: totalParticipationsCount } = useCountUp(computed(() => data.value?.total_participations ?? 0), 600)
const { count: pendingActivitiesCount } = useCountUp(computed(() => data.value?.pending_activities ?? 0), 600)
const { count: pendingOwnersCount } = useCountUp(computed(() => data.value?.pending_owners ?? 0), 600)
const { count: todayNewCount } = useCountUp(computed(() => data.value?.today_new ?? 0), 600)

// 条形图最大值
const maxTypePercentage = computed(() => {
  if (!data.value?.type_distribution.length) return 100
  return Math.max(...data.value.type_distribution.map((d) => d.percentage))
})

// 活动类型颜色 (基于类型分布数据动态生成)
const CHART_COLORS = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EC4899',
                      '#06B6D4', '#EF4444', '#84CC16', '#F97316', '#6366F1']

const typeColorMap = computed(() => {
  const map: Record<string, string> = {}
  const types = data.value?.type_distribution?.map((d: { type: string }) => d.type) || []
  types.forEach((t: string, i: number) => {
    map[t] = CHART_COLORS[i % CHART_COLORS.length]
  })
  return map
})

function getTypeColor(type: string): string {
  return typeColorMap.value[type] || '#64748B'
}

const maxCollegeCount = computed(() => {
  if (!data.value?.college_distribution.length) return 1
  return Math.max(...data.value.college_distribution.map((d) => d.count))
})

// 日期格式化（保留给统计卡片使用）
function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

// 数字千分位
function formatNum(n: number) {
  return n.toLocaleString('zh-CN')
}

function goToAudit(type: 'activity' | 'owner') {
  if (type === 'activity') router.push('/admin/activity-audit')
  else router.push('/admin/owner-audit')
}

onMounted(() => {
  fetchDashboard()
})
</script>

<template>
  <div class="admin-layout">
    <AdminSidebar />

    <main class="admin-content">
      <!-- 加载骨架 -->
      <template v-if="loading">
        <div class="skeleton-title" />
        <div class="stat-grid">
          <div v-for="i in 6" :key="i" class="skeleton-card" />
        </div>
        <div class="chart-grid">
          <div class="skeleton-chart" />
          <div class="skeleton-chart" />
        </div>
        <div class="skeleton-chart-full" />
      </template>

      <!-- 错误状态 -->
      <template v-else-if="error">
        <div class="error-card">
          <AlertCircle class="w-8 h-8 text-danger" />
          <p class="text-text-primary font-medium">数据加载失败</p>
          <p class="text-text-secondary text-sm">{{ error }}</p>
          <button class="btn-primary mt-4" @click="retry">重新加载</button>
        </div>
      </template>

      <!-- 正常内容 -->
      <template v-else-if="data">
        <h1 class="page-title">数据看板</h1>

        <!-- 核心指标 -->
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-icon" style="background: var(--color-primary-light); color: var(--color-primary)">
              <Users class="w-5 h-5" />
            </div>
            <span class="stat-label">总用户数</span>
            <span class="stat-value">{{ formatNum(totalUsersCount) }}</span>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="background: var(--color-info-light); color: var(--color-info)">
              <CalendarDays class="w-5 h-5" />
            </div>
            <span class="stat-label">总活动数</span>
            <span class="stat-value">{{ formatNum(totalActivitiesCount) }}</span>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="background: var(--color-secondary-light); color: var(--color-secondary)">
              <UserCheck class="w-5 h-5" />
            </div>
            <span class="stat-label">总参与人次</span>
            <span class="stat-value">{{ formatNum(totalParticipationsCount) }}</span>
          </div>
        </div>

        <!-- 待办与动态 -->
        <div class="stat-grid">
          <div class="stat-card stat-card--alert" @click="data.pending_activities > 0 && goToAudit('activity')">
            <div class="stat-icon" style="background: var(--color-accent-light); color: var(--color-accent)">
              <Clock class="w-5 h-5" />
            </div>
            <span class="stat-label">待审活动</span>
            <span class="stat-value">{{ pendingActivitiesCount }}</span>
            <span v-if="data.pending_activities > 0" class="stat-link">
              去审核 <ArrowRight class="w-3.5 h-3.5" />
            </span>
            <span v-else class="stat-link stat-link--muted">暂无待审</span>
          </div>
          <div class="stat-card stat-card--alert" @click="data.pending_owners > 0 && goToAudit('owner')">
            <div class="stat-icon" style="background: var(--color-accent-light); color: var(--color-accent)">
              <Building2 class="w-5 h-5" />
            </div>
            <span class="stat-label">待审主体</span>
            <span class="stat-value">{{ pendingOwnersCount }}</span>
            <span v-if="data.pending_owners > 0" class="stat-link">
              去审核 <ArrowRight class="w-3.5 h-3.5" />
            </span>
            <span v-else class="stat-link stat-link--muted">暂无待审</span>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="background: var(--color-success-light); color: var(--color-success)">
              <TrendingUp class="w-5 h-5" />
            </div>
            <span class="stat-label">今日新增</span>
            <span class="stat-value">{{ todayNewCount }}</span>
          </div>
        </div>

        <!-- 数据分布 -->
        <div class="chart-grid">
          <!-- 活动类型分布 -->
          <div class="chart-card">
            <h3 class="chart-title">活动类型分布</h3>
            <div class="bar-list">
              <div v-for="item in data.type_distribution" :key="item.type" class="bar-row">
                <span class="bar-label">{{ item.type }}</span>
                <div class="bar-track">
                  <div
                    class="bar-fill bar-fill--type"
                    :style="{ width: (item.percentage / maxTypePercentage * 100) + '%', background: getTypeColor(item.type) }"
                  >
                    <span v-if="item.percentage >= 10" class="bar-pct">{{ item.percentage.toFixed(1) }}%</span>
                  </div>
                </div>
                <span class="bar-count">{{ item.count }}</span>
              </div>
            </div>
          </div>

          <!-- 各学院参与人数 -->
          <div class="chart-card">
            <h3 class="chart-title">各学院参与人数</h3>
            <div class="bar-list">
              <div v-for="item in data.college_distribution" :key="item.college" class="bar-row">
                <span class="bar-label bar-label--wide">{{ item.college }}</span>
                <div class="bar-track">
                  <div
                    class="bar-fill bar-fill--college"
                    :style="{ width: (item.count / maxCollegeCount * 100) + '%' }"
                  >
                    <span v-if="(item.count / maxCollegeCount) >= 0.25" class="bar-pct">{{ formatNum(item.count) }}</span>
                  </div>
                </div>
                <span v-if="(item.count / maxCollegeCount) < 0.25" class="bar-count">{{ formatNum(item.count) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 近7天趋势 -->
        <div class="chart-card chart-card--full">
          <h3 class="chart-title">近7天新增活动与参与人次</h3>
          <div class="trend-legend">
            <span class="trend-legend-item">
              <span class="trend-legend-line trend-legend-line--solid" />
              <span class="trend-legend-dot" style="background: #10B981" />
              参与人次
            </span>
            <span class="trend-legend-item">
              <span class="trend-legend-line trend-legend-line--dashed" />
              <span class="trend-legend-dot" style="background: #3B82F6" />
              新增活动
            </span>
          </div>
          <div class="trend-chart-wrap">
            <canvas ref="trendCanvas" style="width:100%; height:220px;"></canvas>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100dvh;
}

.admin-content {
  flex: 1;
  background: var(--color-bg);
  padding: 24px;
  overflow-y: auto;
}

/* ── 页面标题 ── */
.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 24px;
}

/* ── 统计卡片网格 ── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: box-shadow 150ms;
}

.stat-card:hover {
  box-shadow: var(--shadow-card-hover);
}

.stat-card--alert {
  border-left: 3px solid var(--color-accent);
  cursor: default;
}

.stat-card--alert[style*="cursor"] {
  /* 可点击时有手型 */
}

.stat-card--alert:has(.stat-link:not(.stat-link--muted)) {
  cursor: pointer;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: 'MiSans Latin', 'HarmonyOS Sans', monospace;
  line-height: 1.2;
}

.stat-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-accent);
  font-weight: 500;
  margin-top: 2px;
}

.stat-link--muted {
  color: var(--color-text-disabled);
  font-weight: 400;
}

/* ── 图表网格 ── */
.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.chart-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
}

.chart-card--full {
  grid-column: 1 / -1;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 16px;
}

/* ── 横向条形图 ── */
.bar-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-label {
  width: 80px;
  text-align: right;
  font-size: 14px;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.bar-label--wide {
  width: 100px;
}

.bar-track {
  flex: 1;
  height: 28px;
  background: var(--color-surface-alt);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
  min-width: 4px;
  transition: width 600ms ease-out;
}

.bar-fill--type {
  background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
}

.bar-fill--college {
  background: linear-gradient(90deg, var(--color-secondary), var(--color-info));
}

.bar-pct {
  font-size: 12px;
  color: #fff;
  font-weight: 500;
  white-space: nowrap;
}

.bar-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  min-width: 50px;
  text-align: right;
  flex-shrink: 0;
}

/* ── 折线图 ── */
.trend-legend {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
  justify-content: flex-end;
}

.trend-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.trend-legend-line {
  width: 20px;
  height: 2px;
}

.trend-legend-line--solid {
  background: #10B981;
}

.trend-legend-line--dashed {
  background: repeating-linear-gradient(
    90deg,
    #3B82F6 0,
    #3B82F6 6px,
    transparent 6px,
    transparent 9px
  );
}

.trend-legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.trend-chart-wrap {
  position: relative;
  width: 100%;
}

/* ── 骨架屏 ── */
.skeleton-title {
  width: 120px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-alt);
  margin-bottom: 24px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-card {
  height: 120px;
  border-radius: var(--radius-lg);
  background: var(--color-surface-alt);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-chart {
  height: 260px;
  border-radius: var(--radius-lg);
  background: var(--color-surface-alt);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-chart-full {
  height: 260px;
  border-radius: var(--radius-lg);
  background: var(--color-surface-alt);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ── 错误卡片 ── */
.error-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;
  gap: 8px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 24px;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: background 150ms;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

/* ── 减少动效 ── */
@media (prefers-reduced-motion: reduce) {
  .bar-fill {
    transition: none;
  }
  .skeleton-title,
  .skeleton-card,
  .skeleton-chart,
  .skeleton-chart-full {
    animation: none;
  }
}
</style>
