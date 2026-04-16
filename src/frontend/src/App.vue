<template>
  <div class="app-shell">
    <header class="panel topbar">
      <div>
        <h1>Trend Is Your Friend</h1>
        <p>Internal dashboard for stored market views and extraction jobs.</p>
      </div>
      <div class="topbar-status">
        <span class="status-badge" :class="processing ? 'status-running' : 'status-idle'">
          {{ processing ? actionLabel : 'Idle' }}
        </span>
        <div class="status-meta">
          <span><strong>Last run:</strong> {{ status.last_run ? formatDateTime(status.last_run) : 'None' }}</span>
          <span><strong>Coverage:</strong> {{ coverageWindow }}</span>
        </div>
      </div>
    </header>

    <nav class="panel tabs">
      <button
        type="button"
        class="tab-button"
        :class="{ active: activeTab === 'analytics' }"
        @click="activeTab = 'analytics'"
      >
        Analytics
      </button>
      <button
        type="button"
        class="tab-button"
        :class="{ active: activeTab === 'pipeline' }"
        @click="activeTab = 'pipeline'"
      >
        Pipeline
      </button>
    </nav>

    <section v-if="activeTab === 'analytics'" class="tab-layout">
      <article class="panel section-panel">
        <div class="section-header">
          <div>
            <h2>Filters</h2>
            <p>Filter by dates, underlying, bank, sentiment, or text.</p>
          </div>
          <div class="section-actions">
            <button class="btn-primary" :disabled="loading" @click="applyFilters">Apply</button>
            <button class="btn-secondary" :disabled="loading" @click="resetFilters">Clear</button>
          </div>
        </div>

        <div class="form-grid">
          <label class="field field-wide">
            <span>Search</span>
            <input
              v-model="filters.search"
              type="text"
              placeholder="Search rationale, levels, bank, underlying"
              @keyup.enter="applyFilters"
            >
          </label>
          <label class="field">
            <span>Underlying</span>
            <select v-model="filters.underlying">
              <option value="">All</option>
              <option v-for="item in filterMeta.underlyings" :key="item.value" :value="item.value">
                {{ item.value }} ({{ item.count }})
              </option>
            </select>
          </label>
          <label class="field">
            <span>Bank</span>
            <select v-model="filters.bank">
              <option value="">All</option>
              <option v-for="item in filterMeta.banks" :key="item.value" :value="item.value">
                {{ item.value }} ({{ item.count }})
              </option>
            </select>
          </label>
          <label class="field">
            <span>Sentiment</span>
            <select v-model="filters.sentiment">
              <option value="">All</option>
              <option v-for="item in filterMeta.sentiments" :key="item.value" :value="item.value">
                {{ capitalize(item.value) }} ({{ item.count }})
              </option>
            </select>
          </label>
          <label class="field">
            <span>Start date</span>
            <input v-model="filters.start_date" type="date">
          </label>
          <label class="field">
            <span>End date</span>
            <input v-model="filters.end_date" type="date">
          </label>
          <label class="field">
            <span>Sort by</span>
            <select v-model="filters.sort_by">
              <option value="date">Date</option>
              <option value="confidence">Confidence</option>
              <option value="underlying">Underlying</option>
              <option value="bank">Bank</option>
              <option value="sentiment">Sentiment</option>
            </select>
          </label>
          <label class="field">
            <span>Order</span>
            <select v-model="filters.sort_order">
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </label>
        </div>

        <div class="chip-row">
          <span v-for="chip in activeFilterChips" :key="chip.label" class="filter-chip">{{ chip.label }}</span>
          <span v-if="!activeFilterChips.length" class="filter-chip filter-chip-muted">No active filters</span>
        </div>
      </article>

      <section class="stats-grid">
        <article v-for="card in statCards" :key="card.label" class="panel stat-card">
          <span class="stat-label">{{ card.label }}</span>
          <strong class="stat-value">{{ card.value }}</strong>
          <p class="stat-note">{{ card.note }}</p>
        </article>
      </section>

      <section class="panel section-panel">
        <div class="section-header">
          <div>
            <h2>Current slice</h2>
            <p>Quick summary of what matches the current filters.</p>
          </div>
        </div>
        <div class="summary-grid">
          <div class="summary-item">
            <span class="summary-label">Matching rows</span>
            <strong>{{ filterMeta.result_count }}</strong>
          </div>
          <div class="summary-item">
            <span class="summary-label">Average confidence</span>
            <strong>{{ summary.avg_confidence }}%</strong>
          </div>
          <div class="summary-item">
            <span class="summary-label">Date min</span>
            <strong>{{ filterMeta.date_bounds.min ? formatDate(filterMeta.date_bounds.min) : '-' }}</strong>
          </div>
          <div class="summary-item">
            <span class="summary-label">Date max</span>
            <strong>{{ filterMeta.date_bounds.max ? formatDate(filterMeta.date_bounds.max) : '-' }}</strong>
          </div>
        </div>
      </section>

      <section class="charts-grid">
        <article class="panel chart-panel">
          <div class="section-header compact">
            <div>
              <h2>Sentiment</h2>
              <p>Distribution of bullish, bearish, and neutral views.</p>
            </div>
          </div>
          <SentimentChart :items="dashboard.sentiment_breakdown" />
        </article>

        <article class="panel chart-panel">
          <div class="section-header compact">
            <div>
              <h2>Confidence</h2>
              <p>How strong the extracted views are.</p>
            </div>
          </div>
          <ConfidenceChart :items="dashboard.confidence_breakdown" />
        </article>

        <article class="panel chart-panel">
          <div class="section-header compact">
            <div>
              <h2>Timeline</h2>
              <p>Views and average confidence by date.</p>
            </div>
          </div>
          <TimelineChart :items="dashboard.timeline" />
        </article>

        <article class="panel chart-panel">
          <div class="section-header compact">
            <div>
              <h2>Top banks</h2>
              <p>Which banks appear most in the stored views.</p>
            </div>
          </div>
          <RankingChart :items="dashboard.top_banks" color="#2563eb" />
        </article>
      </section>

      <section class="lists-grid">
        <article class="panel section-panel">
          <div class="section-header compact">
            <div>
              <h2>Top underlyings</h2>
              <p>Most represented assets in the current slice.</p>
            </div>
          </div>
          <div v-if="dashboard.top_underlyings.length" class="simple-list">
            <button
              v-for="item in dashboard.top_underlyings"
              :key="item.label"
              class="simple-row"
              @click="applyQuickFilter('underlying', item.label)"
            >
              <span>{{ item.label }}</span>
              <span>{{ item.count }} views | {{ item.avg_confidence }}%</span>
            </button>
          </div>
          <p v-else class="empty-copy">No underlyings for the current filters.</p>
        </article>

        <article class="panel section-panel">
          <div class="section-header compact">
            <div>
              <h2>Recent views</h2>
              <p>Latest rows stored in the current slice.</p>
            </div>
          </div>
          <div v-if="dashboard.recent_views.length" class="simple-list">
            <button
              v-for="view in dashboard.recent_views"
              :key="view.id"
              class="simple-row"
              @click="applyQuickFilter('underlying', view.underlying)"
            >
              <span>{{ view.underlying }} | {{ view.bank }}</span>
              <span>{{ view.sentiment }} | {{ view.confidence }}%</span>
            </button>
          </div>
          <p v-else class="empty-copy">No recent views for the current filters.</p>
        </article>
      </section>

      <section class="panel section-panel table-panel">
        <div class="section-header">
          <div>
            <h2>Views table</h2>
            <p>Detailed stored rows with quick filters.</p>
          </div>
          <div class="section-actions">
            <span class="table-meta">{{ views.length }} rows</span>
            <button class="btn-secondary" :disabled="loading" @click="refreshDashboard">Reload</button>
          </div>
        </div>

        <div v-if="loading" class="loading-state">Refreshing data...</div>
        <div v-else-if="error" class="message error-message">{{ error }}</div>
        <div v-else-if="!views.length" class="empty-state">No rows match the current filters.</div>
        <div v-else class="table-wrapper">
          <table class="views-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Underlying</th>
                <th>Sentiment</th>
                <th>Bank</th>
                <th>Confidence</th>
                <th>Levels</th>
                <th>Rationale</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="view in views" :key="view.id">
                <td>{{ formatDate(view.date) }}</td>
                <td>
                  <button class="table-chip" @click="applyQuickFilter('underlying', view.underlying)">
                    {{ view.underlying }}
                  </button>
                </td>
                <td>
                  <span class="sentiment-pill" :class="`sentiment-${view.sentiment}`">{{ view.sentiment }}</span>
                </td>
                <td>
                  <button class="table-chip table-chip-muted" @click="applyQuickFilter('bank', view.bank)">
                    {{ view.bank }}
                  </button>
                </td>
                <td>{{ view.confidence }}%</td>
                <td>{{ view.levels || '-' }}</td>
                <td class="rationale-cell">{{ view.rationale || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </section>

    <section v-else class="tab-layout">
      <div class="pipeline-grid">
        <article class="panel section-panel">
          <div class="section-header">
            <div>
              <h2>Run pipeline</h2>
              <p>Fetch new Outlook emails or backfill emails already stored in the database.</p>
            </div>
          </div>

          <div class="form-grid">
            <label class="field">
              <span>Start date</span>
              <input v-model="processForm.start_date" type="date">
            </label>
            <label class="field">
              <span>End date</span>
              <input v-model="processForm.end_date" type="date">
            </label>
            <label class="field">
              <span>Provider</span>
              <select v-model="processForm.provider">
                <option value="openai">OpenAI</option>
                <option value="ollama">Ollama</option>
              </select>
            </label>
            <label class="field">
              <span>Model</span>
              <input v-model="processForm.model" type="text" placeholder="gpt-4o-mini">
            </label>
          </div>

          <div class="toggle-row">
            <label class="toggle">
              <input v-model="processForm.strict" type="checkbox">
              <span>Strict filtering</span>
            </label>
            <label class="toggle">
              <input v-model="processForm.refresh" type="checkbox">
              <span>Refresh date range</span>
            </label>
          </div>

          <div class="section-actions">
            <button class="btn-primary" :disabled="processing" @click="triggerProcessing">
              {{ processing && status.current_action === 'process_emails' ? 'Fetching...' : 'Fetch from Outlook' }}
            </button>
            <button class="btn-secondary" :disabled="processing" @click="triggerBackfill">
              {{ processing && status.current_action === 'backfill_missing_views' ? 'Backfilling...' : 'Backfill stored emails' }}
            </button>
          </div>

          <div v-if="processMessage" class="message success-message">{{ processMessage }}</div>
          <div v-if="processError" class="message error-message">{{ processError }}</div>
        </article>

        <article class="panel section-panel">
          <div class="section-header">
            <div>
              <h2>Status</h2>
              <p>Latest processing metadata returned by the backend.</p>
            </div>
          </div>

          <div class="status-grid">
            <div class="summary-item">
              <span class="summary-label">Current action</span>
              <strong>{{ status.current_action || 'None' }}</strong>
            </div>
            <div class="summary-item">
              <span class="summary-label">Processing</span>
              <strong>{{ processing ? 'Yes' : 'No' }}</strong>
            </div>
            <div class="summary-item">
              <span class="summary-label">Last run</span>
              <strong>{{ status.last_run ? formatDateTime(status.last_run) : 'None' }}</strong>
            </div>
            <div class="summary-item">
              <span class="summary-label">Latest result</span>
              <strong>{{ latestResultLabel || 'No result yet' }}</strong>
            </div>
          </div>

          <div v-if="lastResultRows.length" class="result-grid">
            <div v-for="row in lastResultRows" :key="row.label" class="result-row">
              <span>{{ row.label }}</span>
              <strong>{{ row.value }}</strong>
            </div>
          </div>
        </article>
      </div>

      <article class="panel section-panel">
        <div class="section-header compact">
          <div>
            <h2>What each action does</h2>
            <p>Simple separation between ingestion and recovery.</p>
          </div>
        </div>
        <div class="help-grid">
          <div class="help-card">
            <strong>Fetch from Outlook</strong>
            <p>Reads the mailbox, filters emails, sends relevant texts to the LLM, then stores new views in SQLite.</p>
          </div>
          <div class="help-card">
            <strong>Backfill stored emails</strong>
            <p>Reprocesses emails already saved in the database when they exist without associated views.</p>
          </div>
          <div class="help-card">
            <strong>Refresh range</strong>
            <p>Deletes emails and views in the selected date range before rebuilding them from scratch.</p>
          </div>
          <div class="help-card">
            <strong>Strict filtering</strong>
            <p>Uses a stronger pre-filter so only emails with clearer market signals are sent to the LLM.</p>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script>
import axios from 'axios'
import ConfidenceChart from './components/ConfidenceChart.vue'
import RankingChart from './components/RankingChart.vue'
import SentimentChart from './components/SentimentChart.vue'
import TimelineChart from './components/TimelineChart.vue'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const today = new Date().toISOString().slice(0, 10)

const defaultDashboard = () => ({
  summary: {
    total_views: 0,
    avg_confidence: 0,
    bullish_count: 0,
    bearish_count: 0,
    neutral_count: 0,
    unique_underlyings: 0,
    unique_banks: 0,
    latest_date: null
  },
  sentiment_breakdown: [],
  confidence_breakdown: [],
  top_underlyings: [],
  top_banks: [],
  timeline: [],
  recent_views: []
})

const defaultFilterMeta = () => ({
  underlyings: [],
  banks: [],
  sentiments: [],
  date_bounds: { min: null, max: null },
  result_count: 0
})

export default {
  name: 'App',
  components: { ConfidenceChart, RankingChart, SentimentChart, TimelineChart },
  data() {
    return {
      activeTab: 'analytics',
      loading: false,
      processing: false,
      error: null,
      processMessage: null,
      processError: null,
      dashboard: defaultDashboard(),
      filterMeta: defaultFilterMeta(),
      views: [],
      filters: {
        search: '',
        underlying: '',
        bank: '',
        sentiment: '',
        start_date: '',
        end_date: '',
        sort_by: 'date',
        sort_order: 'desc'
      },
      processForm: {
        start_date: today,
        end_date: today,
        refresh: false,
        provider: 'openai',
        model: 'gpt-4o-mini',
        strict: false
      },
      status: {
        processing: false,
        current_action: null,
        last_run: null,
        last_result: null
      },
      statusInterval: null
    }
  },
  computed: {
    summary() {
      return this.dashboard.summary || defaultDashboard().summary
    },
    actionLabel() {
      if (this.status.current_action === 'process_emails') return 'Fetch running'
      if (this.status.current_action === 'backfill_missing_views') return 'Backfill running'
      return 'Processing'
    },
    latestResultLabel() {
      if (!this.status.last_result) return ''
      const action = this.status.last_result.action === 'backfill_missing_views' ? 'Backfill' : 'Fetch'
      return `${action}: ${this.status.last_result.views_created || 0} views created`
    },
    coverageWindow() {
      const minDate = this.filterMeta.date_bounds.min
      const maxDate = this.filterMeta.date_bounds.max
      if (!minDate || !maxDate) return 'No data'
      return `${this.formatDate(minDate)} to ${this.formatDate(maxDate)}`
    },
    activeFilterChips() {
      const chips = []
      if (this.filters.search) chips.push({ label: `Search: ${this.filters.search}` })
      if (this.filters.underlying) chips.push({ label: `Underlying: ${this.filters.underlying}` })
      if (this.filters.bank) chips.push({ label: `Bank: ${this.filters.bank}` })
      if (this.filters.sentiment) chips.push({ label: `Sentiment: ${this.capitalize(this.filters.sentiment)}` })
      if (this.filters.start_date) chips.push({ label: `From: ${this.formatDate(this.filters.start_date)}` })
      if (this.filters.end_date) chips.push({ label: `To: ${this.formatDate(this.filters.end_date)}` })
      return chips
    },
    statCards() {
      return [
        { label: 'Total views', value: this.summary.total_views, note: 'Rows matching current filters.' },
        { label: 'Average confidence', value: `${this.summary.avg_confidence}%`, note: 'Mean confidence for the slice.' },
        { label: 'Bullish', value: this.summary.bullish_count, note: 'Positive directional views.' },
        { label: 'Bearish', value: this.summary.bearish_count, note: 'Negative directional views.' },
        { label: 'Underlyings', value: this.summary.unique_underlyings, note: 'Distinct assets represented.' },
        { label: 'Banks', value: this.summary.unique_banks, note: 'Distinct contributors represented.' }
      ]
    },
    lastResultRows() {
      const result = this.status.last_result
      if (!result) return []
      return [
        { label: 'Action', value: result.action || '-' },
        { label: 'Start date', value: result.start_date || '-' },
        { label: 'End date', value: result.end_date || '-' },
        { label: 'New emails', value: result.new_emails ?? '-' },
        { label: 'Reprocessed emails', value: result.emails_reprocessed ?? '-' },
        { label: 'Sent to LLM', value: result.emails_sent_to_llm ?? '-' },
        { label: 'Views created', value: result.views_created ?? '-' },
        { label: 'Provider', value: result.provider || '-' },
        { label: 'Model', value: result.model || '-' }
      ]
    }
  },
  methods: {
    buildFilterParams(includeSort = false) {
      const params = new URLSearchParams()
      if (this.filters.search) params.append('search', this.filters.search)
      if (this.filters.underlying) params.append('underlying', this.filters.underlying)
      if (this.filters.bank) params.append('bank', this.filters.bank)
      if (this.filters.sentiment) params.append('sentiment', this.filters.sentiment)
      if (this.filters.start_date) params.append('start_date', this.filters.start_date)
      if (this.filters.end_date) params.append('end_date', this.filters.end_date)
      if (includeSort) {
        params.append('sort_by', this.filters.sort_by)
        params.append('sort_order', this.filters.sort_order)
        params.append('limit', '2000')
      }
      return params
    },
    async refreshDashboard() {
      this.loading = true
      this.error = null
      try {
        const filterParams = this.buildFilterParams(false)
        const viewParams = this.buildFilterParams(true)
        const [dashboardResponse, metaResponse, viewsResponse] = await Promise.all([
          axios.get(`${API_URL}/dashboard?${filterParams}`),
          axios.get(`${API_URL}/filters/meta?${filterParams}`),
          axios.get(`${API_URL}/views?${viewParams}`)
        ])
        this.dashboard = dashboardResponse.data
        this.filterMeta = metaResponse.data
        this.views = viewsResponse.data
      } catch (err) {
        this.error = `Unable to load data: ${err.response?.data?.detail || err.message}`
        console.error(err)
      } finally {
        this.loading = false
      }
    },
    async fetchStatus() {
      try {
        const response = await axios.get(`${API_URL}/status`)
        this.status = response.data
        this.processing = response.data.processing
      } catch (err) {
        console.warn('Unable to fetch status', err)
      }
    },
    async triggerProcessing() {
      this.processing = true
      this.processError = null
      this.processMessage = null
      try {
        const response = await axios.post(`${API_URL}/process`, this.processForm)
        this.processMessage =
          `Processed ${response.data.new_emails || 0} new emails, reprocessed ${response.data.emails_reprocessed || 0}, ` +
          `and created ${response.data.views_created || 0} views.`
        await this.refreshDashboard()
        await this.fetchStatus()
      } catch (err) {
        this.processError = `Processing failed: ${err.response?.data?.detail || err.message}`
        console.error(err)
      } finally {
        this.processing = false
      }
    },
    async triggerBackfill() {
      this.processing = true
      this.processError = null
      this.processMessage = null
      try {
        const payload = {
          start_date: this.processForm.start_date,
          end_date: this.processForm.end_date,
          provider: this.processForm.provider,
          model: this.processForm.model
        }
        const response = await axios.post(`${API_URL}/backfill-missing-views`, payload)
        this.processMessage =
          `Backfill completed: ${response.data.emails_reprocessed || 0} emails replayed and ${response.data.views_created || 0} views created.`
        await this.refreshDashboard()
        await this.fetchStatus()
      } catch (err) {
        this.processError = `Backfill failed: ${err.response?.data?.detail || err.message}`
        console.error(err)
      } finally {
        this.processing = false
      }
    },
    applyFilters() {
      this.refreshDashboard()
    },
    resetFilters() {
      this.filters = {
        search: '',
        underlying: '',
        bank: '',
        sentiment: '',
        start_date: '',
        end_date: '',
        sort_by: 'date',
        sort_order: 'desc'
      }
      this.refreshDashboard()
    },
    applyQuickFilter(key, value) {
      this.filters[key] = value
      this.activeTab = 'analytics'
      this.refreshDashboard()
    },
    formatDate(value) {
      if (!value) return '-'
      return new Intl.DateTimeFormat(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      }).format(new Date(value))
    },
    formatDateTime(value) {
      if (!value) return '-'
      return new Intl.DateTimeFormat(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(new Date(value))
    },
    capitalize(value) {
      if (!value) return ''
      return value.charAt(0).toUpperCase() + value.slice(1)
    }
  },
  mounted() {
    this.refreshDashboard()
    this.fetchStatus()
    this.statusInterval = setInterval(this.fetchStatus, 5000)
  },
  beforeUnmount() {
    if (this.statusInterval) clearInterval(this.statusInterval)
  }
}
</script>
