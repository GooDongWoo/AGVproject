<template>
  <div class="app-container">
    <!-- 클릭 가능한 제목 -->
    <h1 class="main-title clickable" @click="goToMainPage">스마트 물류 관리 UI</h1>
    
    <!-- AGV 선택 상태 표시 (상세 페이지에서만) -->
    <div v-if="selectedAgv" class="selected-agv-indicator">
      <span class="selected-text">선택된 AGV:</span>
      <span class="selected-agv">AGV {{ selectedAgv }}</span>
      <span 
        :class="['status-indicator', getAgvStatus(selectedAgv).isWorking ? 'working' : 'idle']"
      ></span>
    </div>

    <!-- 메인 페이지 (AGV 선택 전) -->
    <div v-if="!selectedAgv" class="main-page">
      <div class="welcome-section">
        <h2>📊 AGV 모니터링 시스템</h2>
        <p>실시간으로 AGV의 작업 상태와 성과를 모니터링하세요</p>
      </div>
      
      <div class="agv-overview">
        <h3>AGV 현황</h3>
        <div class="agv-cards">
          <div 
            v-for="agvId in agvList" 
            :key="agvId"
            class="agv-overview-card"
            @click="selectAgv(agvId)"
          >
            <div class="agv-card-header">
              <h4>AGV {{ agvId }}</h4>
              <span 
                :class="['status-badge', getAgvStatus(agvId).isWorking ? 'working' : 'idle']"
              >
                {{ getAgvStatus(agvId).statusText }}
              </span>
            </div>
            <div class="agv-card-stats">
              <div class="stat">
                <span class="stat-label">완료 작업</span>
                <span class="stat-value">{{ getAgvStats(agvId).completedTasks }}</span>
              </div>
              <div class="stat">
                <span class="stat-label">평균 시간</span>
                <span class="stat-value">{{ getAgvStats(agvId).avgTime }}분</span>
              </div>
              <div class="stat">
                <span class="stat-label">총 충돌</span>
                <span class="stat-value">{{ getAgvStats(agvId).totalCollisions }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 실시간 AI 분석 -->
      <div class="ai-analysis-overview">
        <h3>🤖 실시간 AI 분석</h3>
        <div class="ai-analysis-cards">
          <div 
            v-for="agvId in agvList" 
            :key="agvId"
            class="ai-analysis-card"
            @click="selectAgv(agvId)"
          >
            <div class="ai-card-header">
              <div class="ai-card-title">
                <span class="ai-icon">🤖</span>
                <h4>AGV {{ agvId }} 분석</h4>
              </div>
              <div class="ai-status">
                <span :class="['ai-status-badge', getAiAnalysisStatus(agvId)]">
                  {{ getAiAnalysisStatusText(agvId) }}
                </span>
              </div>
            </div>
            
            <div class="ai-comment-section">
              <h5>💬 AI 코멘트</h5>
              <p class="ai-comment">{{ getAiComment(agvId) }}</p>
            </div>
            
            <div class="ai-suggestions-section">
              <h5>💡 개선 사항</h5>
              <ul class="ai-suggestions">
                <li 
                  v-for="suggestion in getAiSuggestions(agvId)" 
                  :key="suggestion"
                  class="ai-suggestion"
                >
                  {{ suggestion }}
                </li>
              </ul>
            </div>
            
            <div class="ai-metrics" :style="{ display: 'flex', flexDirection: 'row', gap: '8px', justifyContent: 'space-between' }">
              <div class="ai-metric">
                <span class="metric-label">효율성 점수</span>
                <span class="metric-value">{{ getEfficiencyScore(agvId) }}%</span>
              </div>
              <div class="ai-metric">
                <span class="metric-label">안전성 등급</span>
                <span class="metric-value">{{ getSafetyGrade(agvId) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 섹션별 물류 현황 -->
      <div class="logistics-overview">
        <h3>섹션별 물류 현황</h3>
        <div class="logistics-sections">
          <!-- Red Section -->
          <div class="logistics-section red-section">
            <div class="section-header">
              <div class="section-title">
                <div class="section-icon red"></div>
                <h4>Red Section</h4>
              </div>
              <div class="section-status">
                <span :class="['capacity-status', getCapacityStatus('red')]">
                  {{ getCapacityStatusText('red') }}
                </span>
              </div>
            </div>
            
            <div class="logistics-stats">
              <div class="logistics-stat">
                <span class="stat-label">현재 물류량</span>
                <div class="editable-stat">
                  <input 
                    v-if="editingSection === 'red' && editingField === 'current'"
                    v-model.number="tempValue"
                    @blur="saveCapacity('red')"
                    @keyup.enter="saveCapacity('red')"
                    @keyup.escape="cancelEdit"
                    type="number"
                    min="0"
                    class="capacity-input"
                  />
                  <span 
                    v-else
                    @click="editCapacity('red', 'current')"
                    class="stat-value current clickable"
                  >
                    {{ logisticsData.red.current }}
                  </span>
                  <span class="stat-unit">개</span>
                  <button 
                    v-if="editingSection !== 'red' || editingField !== 'current'"
                    @click="editCapacity('red', 'current')"
                    class="edit-button"
                  >
                    ✏️
                  </button>
                </div>
              </div>
              
              <div class="logistics-stat">
                <span class="stat-label">여유 물류량</span>
                <div class="editable-stat">
                  <input 
                    v-if="editingSection === 'red' && editingField === 'capacity'"
                    v-model.number="tempValue"
                    @blur="saveCapacity('red')"
                    @keyup.enter="saveCapacity('red')"
                    @keyup.escape="cancelEdit"
                    type="number"
                    min="0"
                    class="capacity-input"
                  />
                  <span 
                    v-else
                    @click="editCapacity('red', 'capacity')"
                    class="stat-value capacity clickable"
                  >
                    {{ logisticsData.red.capacity }}
                  </span>
                  <span class="stat-unit">개</span>
                  <button 
                    v-if="editingSection !== 'red' || editingField !== 'capacity'"
                    @click="editCapacity('red', 'capacity')"
                    class="edit-button"
                  >
                    ✏️
                  </button>
                </div>
              </div>
              
              <div class="logistics-stat">
                <span class="stat-label">사용률</span>
                <span class="stat-value usage">{{ getUsagePercentage('red') }}%</span>
              </div>
            </div>
            
            <!-- 진행 바 -->
            <div class="progress-container">
              <div class="progress-bar">
                <div 
                  class="progress-fill red"
                  :style="{ width: getUsagePercentage('red') + '%' }"
                ></div>
              </div>
              <span class="progress-text">
                {{ logisticsData.red.current }} / {{ logisticsData.red.capacity }} 개
              </span>
            </div>
          </div>

          <!-- Green Section -->
          <div class="logistics-section green-section">
            <div class="section-header">
              <div class="section-title">
                <div class="section-icon green"></div>
                <h4>Green Section</h4>
              </div>
              <div class="section-status">
                <span :class="['capacity-status', getCapacityStatus('green')]">
                  {{ getCapacityStatusText('green') }}
                </span>
              </div>
            </div>
            
            <div class="logistics-stats">
              <div class="logistics-stat">
                <span class="stat-label">현재 물류량</span>
                <div class="editable-stat">
                  <input 
                    v-if="editingSection === 'green' && editingField === 'current'"
                    v-model.number="tempValue"
                    @blur="saveCapacity('green')"
                    @keyup.enter="saveCapacity('green')"
                    @keyup.escape="cancelEdit"
                    type="number"
                    min="0"
                    class="capacity-input"
                  />
                  <span 
                    v-else
                    @click="editCapacity('green', 'current')"
                    class="stat-value current clickable"
                  >
                    {{ logisticsData.green.current }}
                  </span>
                  <span class="stat-unit">개</span>
                  <button 
                    v-if="editingSection !== 'green' || editingField !== 'current'"
                    @click="editCapacity('green', 'current')"
                    class="edit-button"
                  >
                    ✏️
                  </button>
                </div>
              </div>
              
              <div class="logistics-stat">
                <span class="stat-label">여유 물류량</span>
                <div class="editable-stat">
                  <input 
                    v-if="editingSection === 'green' && editingField === 'capacity'"
                    v-model.number="tempValue"
                    @blur="saveCapacity('green')"
                    @keyup.enter="saveCapacity('green')"
                    @keyup.escape="cancelEdit"
                    type="number"
                    min="0"
                    class="capacity-input"
                  />
                  <span 
                    v-else
                    @click="editCapacity('green', 'capacity')"
                    class="stat-value capacity clickable"
                  >
                    {{ logisticsData.green.capacity }}
                  </span>
                  <span class="stat-unit">개</span>
                  <button 
                    v-if="editingSection !== 'green' || editingField !== 'capacity'"
                    @click="editCapacity('green', 'capacity')"
                    class="edit-button"
                  >
                    ✏️
                  </button>
                </div>
              </div>
              
              <div class="logistics-stat">
                <span class="stat-label">사용률</span>
                <span class="stat-value usage">{{ getUsagePercentage('green') }}%</span>
              </div>
            </div>
            
            <!-- 진행 바 -->
            <div class="progress-container">
              <div class="progress-bar">
                <div 
                  class="progress-fill green"
                  :style="{ width: getUsagePercentage('green') + '%' }"
                ></div>
              </div>
              <span class="progress-text">
                {{ logisticsData.green.current }} / {{ logisticsData.green.capacity }} 개
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 선택된 AGV 상세 페이지 -->
    <div v-if="selectedAgv" class="agv-detail-page">
      <div class="agv-header">
        <div class="agv-title-section">
          <h2>AGV {{ selectedAgv }} 상세 정보</h2>
          <button class="back-button" @click="goToMainPage">← 메인으로</button>
        </div>
        
        <div class="agv-status">
          <div v-if="currentWork[selectedAgv]" class="status-card working">
            <h3>🔄 작업 진행 중</h3>
            <p><strong>작업 ID:</strong> {{ currentWork[selectedAgv].workId }}</p>
            <p><strong>시작 시간:</strong> {{ formatTime(currentWork[selectedAgv].startTime) }}</p>
            <p><strong>진행 시간:</strong> {{ getCurrentWorkDuration(selectedAgv) }}초</p>
          </div>
          <div v-else class="status-card idle">
            <h3>⏸️ 대기 중</h3>
            <p>현재 진행 중인 작업이 없습니다.</p>
          </div>
        </div>
      </div>

      <!-- 시각화 컨테이너 -->
      <div class="chart-container">
        <div class="left-container">
          <!-- 명령어 차트 -->
          <div class="command-chart">
            <div v-if="commandLoading">명령어 데이터 로딩 중...</div>
            <CommandPolarChart 
              v-else 
              :labels="commandLabels" 
              :data="commandData" 
            />
          </div>
          
          <!-- 현재 작업 정보 -->
          <div class="sensing-data-container">
            <div class="num1-container">
              <div>
                <h2 class="num-title">현재 소모 시간</h2>
                <p class="num-data">{{ getCurrentWorkDuration(selectedAgv) }}</p>
                <p>초</p>
              </div>
            </div>
            <div class="num2-container">
              <div>
                <h2 class="num-title">현재 충돌 횟수</h2>
                <p class="num-data">{{ currentCollisions[selectedAgv] || 0 }}</p>
                <p>회</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 완료된 작업 히스토리 차트 -->
        <div class="right-container">
          <div v-if="historyLoading">히스토리 데이터 로딩 중...</div>
          <SensingLineChart 
            v-else 
            :labels="historyLabels" 
            :num1Data="historyDurationData" 
            :num2Data="historyCollisionData"
            :workIds="workIds"
            :title="`AGV ${selectedAgv} 완료 작업 히스토리`"
          />
        </div>
      </div>

      <!-- 완료된 작업 상세보기 섹션 (AGV 상세 페이지에서만 표시) -->
      <div class="task-details-section">
        <h3>AGV {{ selectedAgv }} 완료된 작업 상세보기</h3>
        <div class="task-selector-container">
          <div class="task-selector">
            <label for="task-select">작업 선택:</label>
            <select 
              id="task-select"
              v-model="selectedTaskId"
              @change="selectTask(selectedTaskId)"
              class="task-select"
            >
              <option value="">작업을 선택하세요</option>
              <option 
                v-for="task in availableTasks" 
                :key="task.workId"
                :value="task.workId"
              >
                작업 {{ task.workId }} - {{ formatTime(task.completedAt) }} 완료
              </option>
            </select>
          </div>
          
          <div v-if="selectedTaskData" class="task-info">
            <div class="task-stats">
              <div class="task-stat">
                <span class="stat-label">작업 시간</span>
                <span class="stat-value">{{ Math.floor(selectedTaskData.duration / 60) }}분 {{ selectedTaskData.duration % 60 }}초</span>
              </div>
              <div class="task-stat">
                <span class="stat-label">충돌 횟수</span>
                <span class="stat-value">{{ selectedTaskData.collisions }}회</span>
              </div>
              <div class="task-stat">
                <span class="stat-label">완료 시간</span>
                <span class="stat-value">{{ formatTime(selectedTaskData.completedAt) }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="selectedTaskData" class="task-images">
          <div class="image-container">
            <h4>🎬 작업 시작 화면</h4>
            <div class="image-wrapper">
              <img 
                :src="selectedTaskData.startImage" 
                alt="작업 시작 화면" 
                class="task-image"
              />
              <div class="image-overlay">
                <span class="image-label">Start</span>
              </div>
            </div>
          </div>
          
          <div class="image-container">
            <h4>🏁 작업 완료 화면</h4>
            <div class="image-wrapper">
              <img 
                :src="selectedTaskData.endImage" 
                alt="작업 완료 화면" 
                class="task-image"
              />
              <div class="image-overlay">
                <span class="image-label">End</span>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="!selectedTaskData && availableTasks.length > 0" class="no-task-selected">
          <p>👆 위에서 작업을 선택하면 해당 작업의 시작/완료 화면을 볼 수 있습니다.</p>
        </div>
        
        <div v-if="availableTasks.length === 0" class="no-tasks-available">
          <p>🚫 완료된 작업이 없습니다.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from "vue";
import CommandPolarChart from "./components/CommandPolarChart.vue";
import SensingLineChart from "./components/SensingLineChart.vue";
// 폰트 CSS 파일 import
import "./font.css";

// AGV 관련 상태
const agvList = [1, 2, 3, 4];
const selectedAgv = ref(null);

// 실시간 업데이트를 위한 상태
const currentTime = ref(Date.now());
let timeUpdateInterval = null;

// 로딩 상태
const commandLoading = ref(false);
const historyLoading = ref(false);

// 각 AGV별 데이터 저장
const agvDataStore = ref({
  1: {
    currentWork: {
      workId: 12345,
      startTime: Date.now() - 240000, // 4분 전 시작
    },
    currentCommands: {
      left: 5,
      right: 3,
      up: 2,
      down: 4
    },
    currentCollisions: 1,
    historyData: [
      { workId: 11001, duration: 300, collisions: 2, completedAt: Date.now() - 3600000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 11002, duration: 300, collisions: 1, completedAt: Date.now() - 3300000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 11003, duration: 600, collisions: 0, completedAt: Date.now() - 3000000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 11004, duration: 600, collisions: 3, completedAt: Date.now() - 2700000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 11005, duration: 420, collisions: 1, completedAt: Date.now() - 2400000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 11006, duration: 480, collisions: 2, completedAt: Date.now() - 2100000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 11007, duration: 360, collisions: 0, completedAt: Date.now() - 1800000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 11008, duration: 720, collisions: 4, completedAt: Date.now() - 1500000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 11009, duration: 390, collisions: 1, completedAt: Date.now() - 1200000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 11010, duration: 540, collisions: 2, completedAt: Date.now() - 900000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 11011, duration: 450, collisions: 0, completedAt: Date.now() - 600000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 11012, duration: 660, collisions: 3, completedAt: Date.now() - 300000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' }
    ]
  },
  2: {
    currentWork: null,
    currentCommands: {},
    currentCollisions: 0,
    historyData: [
      { workId: 21001, duration: 480, collisions: 1, completedAt: Date.now() - 2400000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 21002, duration: 360, collisions: 0, completedAt: Date.now() - 1800000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 21003, duration: 720, collisions: 2, completedAt: Date.now() - 1200000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 21004, duration: 420, collisions: 1, completedAt: Date.now() - 900000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 21005, duration: 540, collisions: 0, completedAt: Date.now() - 600000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' }
    ]
  },
  3: {
    currentWork: {
      workId: 33333,
      startTime: Date.now() - 120000, // 2분 전 시작
    },
    currentCommands: {
      left: 2,
      right: 1,
      up: 3,
      down: 2
    },
    currentCollisions: 0,
    historyData: [
      { workId: 31001, duration: 540, collisions: 0, completedAt: Date.now() - 2700000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 31002, duration: 420, collisions: 1, completedAt: Date.now() - 2100000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 31003, duration: 660, collisions: 1, completedAt: Date.now() - 1800000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 31004, duration: 390, collisions: 0, completedAt: Date.now() - 1500000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 31005, duration: 480, collisions: 2, completedAt: Date.now() - 1200000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 31006, duration: 600, collisions: 1, completedAt: Date.now() - 900000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 31007, duration: 360, collisions: 0, completedAt: Date.now() - 600000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 31008, duration: 720, collisions: 3, completedAt: Date.now() - 300000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' }
    ]
  },
  4: {
    currentWork: null,
    currentCommands: {},
    currentCollisions: 0,
    historyData: [
      { workId: 41001, duration: 300, collisions: 1, completedAt: Date.now() - 1800000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 41002, duration: 450, collisions: 0, completedAt: Date.now() - 1200000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 41003, duration: 540, collisions: 2, completedAt: Date.now() - 900000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' },
      { workId: 41004, duration: 390, collisions: 1, completedAt: Date.now() - 600000, startImage: '/api/placeholder/300/200', endImage: '/api/placeholder/300/200' }
    ]
  }
});

// 현재 선택된 AGV의 데이터
const currentWork = ref({});
const currentCommands = ref({});
const currentCollisions = ref({});

// 차트 데이터
const commandLabels = ref([]);
const commandData = ref([]);
const historyLabels = ref([]);
const historyDurationData = ref([]);
const historyCollisionData = ref([]);
const workIds = ref([]);

// 작업 사진 표시 관련 상태
const selectedTaskId = ref(null);
const selectedTaskData = ref(null);
const availableTasks = ref([]);

// 물류 데이터
const logisticsData = ref({
  red: {
    current: 75,
    capacity: 100
  },
  green: {
    current: 45,
    capacity: 80
  }
});

// 편집 관련 상태
const editingSection = ref(null);
const editingField = ref(null); // 'current' 또는 'capacity'
const tempValue = ref(0);

// 메인 페이지로 이동
const goToMainPage = () => {
  selectedAgv.value = null;
  console.log('메인 페이지로 이동');
};

// AGV 선택
const selectAgv = (agvId) => {
  selectedAgv.value = agvId;
  console.log(`AGV ${agvId} 선택됨`);
  loadAgvData(agvId);
};

// AGV 데이터 로드
const loadAgvData = (agvId) => {
  commandLoading.value = true;
  historyLoading.value = true;
  
  const agvData = agvDataStore.value[agvId];
  
  currentWork.value[agvId] = agvData.currentWork;
  currentCommands.value[agvId] = agvData.currentCommands;
  currentCollisions.value[agvId] = agvData.currentCollisions;
  
  commandLabels.value = Object.keys(agvData.currentCommands);
  commandData.value = Object.values(agvData.currentCommands);
  
  // 작업완료시간 순으로 정렬한 후 최근 10개 작업만 표시
  const sortedHistory = [...agvData.historyData].sort((a, b) => a.completedAt - b.completedAt);
  const recentHistory = sortedHistory.slice(-10);
  
  // 완료시간을 날짜/시간 형식으로 변환하고 작업ID 정보도 함께 저장
  historyLabels.value = recentHistory.map(h => {
    const date = new Date(h.completedAt);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${month}/${day} ${hours}:${minutes}`;
  });
  
  // 툴팁용 작업ID 정보도 함께 전달
  workIds.value = recentHistory.map(h => h.workId);
  
  historyDurationData.value = recentHistory.map(h => h.duration);
  historyCollisionData.value = recentHistory.map(h => h.collisions);
  
  // 선택된 AGV의 완료된 작업 목록 업데이트 (전체 히스토리, 최신순)
  availableTasks.value = [...agvData.historyData].sort((a, b) => b.completedAt - a.completedAt);
  
  // 작업 선택 초기화
  selectedTaskId.value = null;
  selectedTaskData.value = null;
  
  setTimeout(() => {
    commandLoading.value = false;
    historyLoading.value = false;
  }, 500);
};

// AGV 상태 가져오기
const getAgvStatus = (agvId) => {
  const hasCurrentWork = agvDataStore.value[agvId].currentWork !== null;
  return {
    isWorking: hasCurrentWork,
    statusText: hasCurrentWork ? '작업중' : '대기중'
  };
};

// AGV 통계 가져오기
const getAgvStats = (agvId) => {
  const historyData = agvDataStore.value[agvId].historyData;
  const completedTasks = historyData.length;
  const avgTime = completedTasks > 0 ? 
    Math.round(historyData.reduce((sum, task) => sum + task.duration, 0) / completedTasks / 60) : 0;
  const totalCollisions = historyData.reduce((sum, task) => sum + task.collisions, 0);
  
  return {
    completedTasks,
    avgTime,
    totalCollisions
  };
};

// 현재 작업 소요 시간 계산 (실시간)
const getCurrentWorkDuration = (agvId) => {
  const work = currentWork.value[agvId];
  if (!work) return 0;
  return Math.floor((currentTime.value - work.startTime) / 1000);
};

// 시간 포맷팅
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('ko-KR');
};

// 물류 용량 편집 함수들
const editCapacity = (section, field = 'capacity') => {
  editingSection.value = section;
  editingField.value = field;
  tempValue.value = logisticsData.value[section][field];
  console.log(`${section} 섹션 ${field} 편집 모드 시작`);
};

const saveCapacity = (section) => {
  if (tempValue.value >= 0) {
    logisticsData.value[section][editingField.value] = tempValue.value;
    console.log(`${section} 섹션 ${editingField.value} 변경: ${tempValue.value}개`);
  }
  editingSection.value = null;
  editingField.value = null;
};

const cancelEdit = () => {
  editingSection.value = null;
  editingField.value = null;
  tempValue.value = 0;
  console.log('편집 취소');
};

// 물류 현황 관련 함수들
const getUsagePercentage = (section) => {
  const data = logisticsData.value[section];
  if (data.capacity === 0) return 0;
  return Math.min(Math.round((data.current / data.capacity) * 100), 100);
};

const getCapacityStatus = (section) => {
  const percentage = getUsagePercentage(section);
  if (percentage >= 90) return 'critical';
  if (percentage >= 70) return 'warning';
  return 'normal';
};

const getCapacityStatusText = (section) => {
  const status = getCapacityStatus(section);
  switch (status) {
    case 'critical': return '위험';
    case 'warning': return '주의';
    default: return '정상';
  }
};

// AI 분석 관련 함수들
const getAiComment = (agvId) => {
  const agvData = agvDataStore.value[agvId];
  const isWorking = agvData.currentWork !== null;
  const recentHistory = agvData.historyData.slice(-5);
  const avgCollisions = recentHistory.reduce((sum, task) => sum + task.collisions, 0) / recentHistory.length;
  const avgDuration = recentHistory.reduce((sum, task) => sum + task.duration, 0) / recentHistory.length;

  if (isWorking) {
    if (avgCollisions > 2) {
      return `AGV ${agvId}는 현재 작업 중이며, 최근 충돌이 자주 발생하고 있습니다. 경로 최적화가 필요해 보입니다.`;
    } else if (avgCollisions < 0.5) {
      return `AGV ${agvId}는 현재 원활하게 작업 중입니다. 충돌 빈도가 낮아 안정적인 운행을 보이고 있습니다.`;
    } else {
      return `AGV ${agvId}는 현재 작업 중이며, 전반적으로 양호한 성능을 보이고 있습니다.`;
    }
  } else {
    if (avgDuration > 600) {
      return `AGV ${agvId}는 대기 상태입니다. 최근 작업 시간이 평균보다 길어 효율성 개선이 필요합니다.`;
    } else {
      return `AGV ${agvId}는 대기 상태입니다. 최근 작업 성과가 양호하여 다음 작업 준비가 완료되었습니다.`;
    }
  }
};

const getAiSuggestions = (agvId) => {
  const agvData = agvDataStore.value[agvId];
  const recentHistory = agvData.historyData.slice(-5);
  const avgCollisions = recentHistory.reduce((sum, task) => sum + task.collisions, 0) / recentHistory.length;
  const avgDuration = recentHistory.reduce((sum, task) => sum + task.duration, 0) / recentHistory.length;
  const suggestions = [];

  if (avgCollisions > 2) {
    suggestions.push('충돌 감지 센서 점검 및 보정');
    suggestions.push('주요 이동 경로 재검토 및 최적화');
  } else if (avgCollisions > 1) {
    suggestions.push('정기적인 센서 청소 및 점검');
  }

  if (avgDuration > 600) {
    suggestions.push('작업 프로세스 효율성 개선');
    suggestions.push('이동 경로 단축 방안 검토');
  } else if (avgDuration < 400) {
    suggestions.push('현재 성능 유지를 위한 정기 점검');
  }

  if (agvData.currentWork && agvData.currentCollisions > 0) {
    suggestions.push('현재 작업 중 충돌 원인 실시간 분석');
  }

  return suggestions.length > 0 ? suggestions : ['현재 최적의 성능을 유지하고 있습니다'];
};

const getEfficiencyScore = (agvId) => {
  const agvData = agvDataStore.value[agvId];
  const recentHistory = agvData.historyData.slice(-5);
  const avgCollisions = recentHistory.reduce((sum, task) => sum + task.collisions, 0) / recentHistory.length;
  const avgDuration = recentHistory.reduce((sum, task) => sum + task.duration, 0) / recentHistory.length;
  
  let score = 100;
  score -= avgCollisions * 10; // 충돌당 10점 차감
  score -= Math.max(0, (avgDuration - 400) / 10); // 기준 시간 초과시 차감
  
  return Math.max(60, Math.round(score));
};

const getSafetyGrade = (agvId) => {
  const agvData = agvDataStore.value[agvId];
  const recentHistory = agvData.historyData.slice(-5);
  const avgCollisions = recentHistory.reduce((sum, task) => sum + task.collisions, 0) / recentHistory.length;
  
  if (avgCollisions >= 3) return 'C';
  if (avgCollisions >= 1.5) return 'B';
  if (avgCollisions >= 0.5) return 'A';
  return 'A+';
};

const getAiAnalysisStatus = (agvId) => {
  const efficiencyScore = getEfficiencyScore(agvId);
  const safetyGrade = getSafetyGrade(agvId);
  
  if (efficiencyScore >= 90 && (safetyGrade === 'A' || safetyGrade === 'A+')) {
    return 'excellent';
  } else if (efficiencyScore >= 80 && safetyGrade !== 'C') {
    return 'good';
  } else if (efficiencyScore >= 70) {
    return 'warning';
  } else {
    return 'critical';
  }
};

const getAiAnalysisStatusText = (agvId) => {
  const status = getAiAnalysisStatus(agvId);
  switch (status) {
    case 'excellent': return '우수';
    case 'good': return '양호';
    case 'warning': return '주의';
    case 'critical': return '개선필요';
    default: return '분석중';
  }
};

// 작업 선택 함수
const selectTask = (taskId) => {
  if (!taskId) {
    selectedTaskId.value = null;
    selectedTaskData.value = null;
    return;
  }
  
  selectedTaskId.value = taskId;
  selectedTaskData.value = availableTasks.value.find(task => task.workId == taskId);
  console.log('선택된 작업:', selectedTaskData.value);
};

onMounted(() => {
  console.log('스마트 물류 관리 UI 시작');
  
  // 실시간 업데이트를 위한 타이머 설정
  timeUpdateInterval = setInterval(() => {
    currentTime.value = Date.now();
  }, 1000);
});

onUnmounted(() => {
  // 컴포넌트 해제시 타이머 정리
  if (timeUpdateInterval) {
    clearInterval(timeUpdateInterval);
  }
});

watch(selectedAgv, (newAgvId) => {
  if (newAgvId) {
    console.log(`AGV ${newAgvId}로 전환`);
    loadAgvData(newAgvId);
  } else {
    console.log('메인 페이지 표시');
  }
});
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  min-height: 100vh;
  background-color: #f8f9fa;
}

.main-title {
  color: #2c3e50;
  margin-bottom: 30px;
  font-size: 2.5rem;
  font-weight: bold;
  transition: all 0.3s ease;
}

.main-title.clickable {
  cursor: pointer;
  user-select: none;
}

.main-title.clickable:hover {
  color: #3498db;
  transform: scale(1.02);
}

.selected-agv-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 30px;
  padding: 15px 25px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  border-left: 4px solid #3498db;
}

.selected-text {
  font-weight: 600;
  color: #7f8c8d;
}

.selected-agv {
  font-weight: bold;
  color: #2c3e50;
  font-size: 1.1rem;
}

.agv-selector {
  display: flex;
  gap: 15px;
  margin-bottom: 30px;
}

.agv-button {
  position: relative;
  padding: 12px 24px;
  border: 2px solid #3498db;
  background-color: white;
  color: #3498db;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: bold;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.agv-button:hover {
  background-color: #3498db;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(52, 152, 219, 0.3);
}

.agv-button.active {
  background-color: #2980b9;
  color: white;
  border-color: #2980b9;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.status-indicator.working {
  background-color: #27ae60;
  animation: pulse 2s infinite;
}

.status-indicator.idle {
  background-color: #95a5a6;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

/* 메인 페이지 스타일 */
.main-page {
  width: 100%;
  max-width: 1200px;
}

.welcome-section {
  text-align: center;
  margin-bottom: 30px;
  padding: 40px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 15px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 120px;
}

.welcome-section h2 {
  margin-bottom: 10px;
  font-size: 1.6rem;
}

.welcome-section p {
  font-size: 1rem;
  opacity: 0.9;
  margin: 0;
}

.agv-overview h3 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
  font-size: 1.8rem;
}

.agv-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.agv-overview-card {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.08);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.agv-overview-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
  border-color: #3498db;
}

.agv-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.agv-card-header h4 {
  color: #2c3e50;
  margin: 0;
  font-size: 1.3rem;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: bold;
}

.status-badge.working {
  background-color: #d5f4e6;
  color: #27ae60;
}

.status-badge.idle {
  background-color: #ecf0f1;
  color: #95a5a6;
}

.agv-card-stats {
  display: flex;
  justify-content: space-between;
}

.stat {
  text-align: center;
}

.stat-label {
  display: block;
  color: #7f8c8d;
  font-size: 0.9rem;
  margin-bottom: 5px;
}

.stat-value {
  display: block;
  color: #2c3e50;
  font-size: 1.4rem;
  font-weight: bold;
}

/* 물류 현황 스타일 */
.logistics-overview {
  margin-top: 0;
  margin-bottom: 40px;
}

.logistics-overview h3 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
  font-size: 1.8rem;
}

.logistics-sections {
  display: flex;
  gap: 30px;
  justify-content: center;
}

.logistics-section {
  background: white;
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  flex: 1;
  max-width: 500px;
  min-width: 350px;
}

.logistics-section:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.logistics-section.red-section {
  border-top: 4px solid #e74c3c;
}

.logistics-section.green-section {
  border-top: 4px solid #27ae60;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
}

.section-icon.red {
  background-color: #e74c3c;
  box-shadow: 0 0 15px rgba(231, 76, 60, 0.4);
}

.section-icon.green {
  background-color: #27ae60;
  box-shadow: 0 0 15px rgba(39, 174, 96, 0.4);
}

.section-title h4 {
  color: #2c3e50;
  margin: 0;
  font-size: 1.5rem;
  font-weight: bold;
}

.capacity-status {
  padding: 8px 16px;
  border-radius: 25px;
  font-size: 0.9rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.capacity-status.normal {
  background-color: #d5f4e6;
  color: #27ae60;
}

.capacity-status.warning {
  background-color: #fef9e7;
  color: #f39c12;
}

.capacity-status.critical {
  background-color: #fadbd8;
  color: #e74c3c;
}

.logistics-stats {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin-bottom: 25px;
  gap: 15px;
}

.logistics-stat {
  text-align: center;
  flex: 1;
}

.logistics-stat .stat-label {
  display: block;
  color: #7f8c8d;
  font-size: 1rem;
  margin-bottom: 10px;
  font-weight: 600;
}

.logistics-stat .stat-value {
  display: inline-block;
  color: #2c3e50;
  font-size: 2.2rem;
  font-weight: bold;
  margin-right: 5px;
}

.logistics-stat .stat-value.current {
  color: #3498db;
}

.logistics-stat .stat-value.capacity {
  color: #8e44ad;
}

.logistics-stat .stat-value.usage {
  color: #e67e22;
}

.logistics-stat .stat-unit {
  color: #95a5a6;
  font-size: 1.1rem;
  font-weight: 500;
}

.editable-stat {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-value.clickable {
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.stat-value.clickable:hover {
  background-color: #f8f9fa;
  color: #8e44ad;
  transform: scale(1.05);
}

.capacity-input {
  width: 90px;
  padding: 8px 12px;
  border: 2px solid #8e44ad;
  border-radius: 8px;
  text-align: center;
  font-size: 2.2rem;
  font-weight: bold;
  color: #2c3e50;
  background-color: #fff;
}

.capacity-input:focus {
  outline: none;
  border-color: #9b59b6;
  box-shadow: 0 0 10px rgba(139, 69, 173, 0.3);
}

.edit-button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 6px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.edit-button:hover {
  background-color: #f8f9fa;
  transform: scale(1.2);
}

.progress-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-bar {
  width: 100%;
  height: 16px;
  background-color: #ecf0f1;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
}

.progress-fill {
  height: 100%;
  border-radius: 8px;
  transition: width 0.5s ease;
  position: relative;
}

.progress-fill.red {
  background: linear-gradient(90deg, #e74c3c 0%, #c0392b 100%);
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.3);
}

.progress-fill.green {
  background: linear-gradient(90deg, #27ae60 0%, #229954 100%);
  box-shadow: 0 2px 8px rgba(39, 174, 96, 0.3);
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-text {
  text-align: center;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

/* AI 분석 현황 스타일 */
.ai-analysis-overview {
  margin-top: 50px;
}

.ai-analysis-overview h3 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
  font-size: 1.8rem;
}

.ai-analysis-cards {
  display: flex;
  gap: 20px;
  justify-content: space-between;
  overflow-x: auto;
  padding-bottom: 10px;
}

.ai-analysis-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.12);
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  position: relative;
  overflow: hidden;
  flex: 1;
  min-width: 280px;
  max-width: 320px;
}

.ai-analysis-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.ai-analysis-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.18);
}

.ai-analysis-card:hover::before {
  opacity: 1;
}

.ai-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.ai-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-icon {
  font-size: 1.2rem;
  animation: pulse-ai 2s infinite;
}

@keyframes pulse-ai {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.ai-card-title h4 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: bold;
}

.ai-status-badge {
  padding: 4px 10px;
  border-radius: 15px;
  font-size: 0.75rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.ai-status-badge.excellent {
  background-color: rgba(46, 204, 113, 0.3);
  color: #2ecc71;
  border: 1px solid rgba(46, 204, 113, 0.5);
}

.ai-status-badge.good {
  background-color: rgba(52, 152, 219, 0.3);
  color: #3498db;
  border: 1px solid rgba(52, 152, 219, 0.5);
}

.ai-status-badge.warning {
  background-color: rgba(241, 196, 15, 0.3);
  color: #f1c40f;
  border: 1px solid rgba(241, 196, 15, 0.5);
}

.ai-status-badge.critical {
  background-color: rgba(231, 76, 60, 0.3);
  color: #e74c3c;
  border: 1px solid rgba(231, 76, 60, 0.5);
}

.ai-comment-section {
  margin-bottom: 12px;
}

.ai-comment-section h5 {
  margin: 0 0 6px 0;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 6px;
  opacity: 0.9;
}

.ai-comment {
  background: rgba(255, 255, 255, 0.1);
  padding: 10px;
  border-radius: 8px;
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.4;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ai-suggestions-section {
  margin-bottom: 12px;
}

.ai-suggestions-section h5 {
  margin: 0 0 6px 0;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 6px;
  opacity: 0.9;
}

.ai-suggestions {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 80px;
  overflow-y: auto;
}

.ai-suggestion {
  background: rgba(255, 255, 255, 0.1);
  padding: 6px 10px;
  border-radius: 6px;
  margin-bottom: 4px;
  font-size: 0.75rem;
  border-left: 2px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(5px);
  transition: all 0.2s ease;
  line-height: 1.3;
}

.ai-suggestion:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateX(3px);
}

.ai-suggestion:last-child {
  margin-bottom: 0;
}

.ai-metric {
  background: rgba(255, 255, 255, 0.1);
  padding: 8px;
  border-radius: 8px;
  text-align: center;
  flex: 1;
  min-width: 0;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.metric-label {
  display: block;
  font-size: 0.6rem;
  opacity: 0.8;
  margin-bottom: 2px;
}

.metric-value {
  display: block;
  font-size: 0.85rem;
  font-weight: bold;
}

/* AGV 상세 페이지 스타일 */
.agv-detail-page {
  width: 100%;
  max-width: 1400px;
}

.agv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 20px;
}

.agv-title-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.agv-title-section h2 {
  color: #2c3e50;
  margin: 0;
}

.back-button {
  padding: 10px 20px;
  background-color: #95a5a6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.back-button:hover {
  background-color: #7f8c8d;
  transform: translateX(-2px);
}

.agv-status {
  display: flex;
  align-items: center;
}

.status-card {
  background-color: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  min-width: 300px;
}

.status-card.working {
  border-left: 4px solid #27ae60;
}

.status-card.idle {
  border-left: 4px solid #95a5a6;
}

.status-card h3 {
  margin: 0 0 10px 0;
  color: #2c3e50;
}

.status-card p {
  margin: 5px 0;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.chart-container {
  background-color: #F4F5FC;
  width: 100%;
  height: 600px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  padding: 20px;
  gap: 20px;
}

.left-container {
  width: 42%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 20px;
}

.right-container {
  background-color: white;
  width: 56%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.command-chart {
  background-color: white;
  width: 100%;
  height: 55%;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.sensing-data-container {
  width: 100%;
  height: 40%;
  display: flex;
  gap: 15px;
}

.num1-container,
.num2-container {
  background-color: white;
  width: 50%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.num1-container > div,
.num2-container > div {
  text-align: center;
}

.num-title {
  color: #8D98A6;
  margin-bottom: 10px;
  font-size: 1.1rem;
}

.num-data {
  font-size: 2.5rem;
  font-weight: bold;
  margin: 15px 0;
  color: #2c3e50;
}

/* 작업 상세보기 섹션 스타일 */
.task-details-section {
  width: 100%;
  max-width: 1400px;
  margin-top: 30px;
  background-color: white;
  border-radius: 15px;
  padding: 25px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.task-details-section h3 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 1.5rem;
  text-align: center;
}

.task-selector-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
}

.task-selector {
  display: flex;
  align-items: center;
  gap: 15px;
  justify-content: center;
}

.task-selector label {
  font-weight: 600;
  color: #2c3e50;
  font-size: 1.1rem;
}

.task-select {
  padding: 10px 15px;
  border: 2px solid #3498db;
  border-radius: 8px;
  font-size: 1rem;
  background-color: white;
  color: #2c3e50;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 300px;
}

.task-select:focus {
  outline: none;
  border-color: #2980b9;
  box-shadow: 0 0 10px rgba(52, 152, 219, 0.3);
}

.task-select:hover {
  border-color: #2980b9;
}

.task-info {
  display: flex;
  justify-content: center;
}

.task-stats {
  display: flex;
  gap: 30px;
  background-color: #f8f9fa;
  padding: 15px 25px;
  border-radius: 10px;
  border: 1px solid #e9ecef;
}

.task-stat {
  text-align: center;
}

.task-stat .stat-label {
  display: block;
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 5px;
}

.task-stat .stat-value {
  display: block;
  font-size: 1.1rem;
  font-weight: bold;
  color: #2c3e50;
}

.task-images {
  display: flex;
  gap: 30px;
  justify-content: center;
  margin-top: 20px;
}

.image-container {
  flex: 1;
  max-width: 400px;
}

.image-container h4 {
  color: #2c3e50;
  margin-bottom: 15px;
  text-align: center;
  font-size: 1.2rem;
}

.image-wrapper {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 6px 20px rgba(0,0,0,0.15);
  transition: all 0.3s ease;
}

.image-wrapper:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.2);
}

.task-image {
  width: 100%;
  height: 250px;
  object-fit: cover;
  display: block;
}

.image-overlay {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: bold;
}

.no-task-selected {
  text-align: center;
  padding: 40px 20px;
  color: #6c757d;
  font-size: 1.1rem;
  background-color: #f8f9fa;
  border-radius: 10px;
  border: 2px dashed #dee2e6;
}

.no-tasks-available {
  text-align: center;
  padding: 40px 20px;
  color: #6c757d;
  font-size: 1.1rem;
  background-color: #fff3cd;
  border-radius: 10px;
  border: 2px dashed #ffeaa7;
}

/* 반응형 디자인 */
@media (max-width: 1200px) {
  .chart-container {
    flex-direction: column;
    height: auto;
    min-height: 800px;
  }
  
  .left-container,
  .right-container {
    width: 100%;
    height: 400px;
  }
  
  .left-container {
    flex-direction: row;
  }
  
  .command-chart {
    width: 50%;
    height: 100%;
  }
  
  .sensing-data-container {
    width: 50%;
    height: 100%;
    flex-direction: column;
  }
  
  .logistics-sections {
    flex-direction: column;
    align-items: center;
  }
  
  .logistics-section {
    max-width: 600px;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .selected-agv-indicator {
    padding: 12px 20px;
    flex-wrap: wrap;
    justify-content: center;
    text-align: center;
  }
  
  .agv-header {
    flex-direction: column;
    text-align: center;
  }
  
  .agv-title-section {
    flex-direction: column;
  }
  
  .left-container {
    flex-direction: column;
  }
  
  .command-chart {
    width: 100%;
    height: 50%;
  }
  
  .sensing-data-container {
    width: 100%;
    height: 50%;
    flex-direction: row;
  }
  
  .agv-cards {
    grid-template-columns: 1fr;
  }
  
  .logistics-sections {
    flex-direction: column;
    gap: 20px;
  }
  
  .logistics-stats {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .logistics-stat {
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 8px;
  }
  
  .logistics-section {
    padding: 20px;
    min-width: auto;
  }
  
  .section-title h4 {
    font-size: 1.3rem;
  }
  
  .logistics-stat .stat-value {
    font-size: 1.8rem;
  }
  
  .ai-analysis-cards {
    flex-direction: column;
    gap: 15px;
  }
  
  .ai-analysis-card {
    min-width: auto;
    max-width: none;
    padding: 15px;
  }

  .ai-comment {
    font-size: 0.75rem;
    max-height: none;
  }
  
  .ai-suggestion {
    font-size: 0.7rem;
  }
  
  .ai-suggestions {
    max-height: none;
  }
  
  .task-images {
    flex-direction: column;
    gap: 20px;
  }
  
  .task-stats {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .task-selector {
    flex-direction: column;
    gap: 10px;
  }
  
  .task-select {
    min-width: auto;
    width: 100%;
  }
  
  .task-details-section {
    padding: 20px;
  }
}
</style>