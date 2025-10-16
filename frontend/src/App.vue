<template>
  <div class="root" :class="{ 'sidebar-hidden': !isSidebarVisible }">
    <!-- 遮罩层，点击后隐藏侧边栏 -->
    <div 
      class="sidebar-overlay" 
      v-if="isSidebarVisible" 
      @click="isSidebarVisible = false"
    ></div>
    
    <div class="sidebar">
      <div class="top">
        <button class="newdialogue" @click="createNewDialogue">
          <img src="/new_dialogue.svg" alt="新建对话" class="icon">
          新建对话
        </button>
        <button class="hidesidebar" @click="toggleSidebar">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M10 12L6 8L10 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      <div class="list">
        <div 
          v-for="item in history" 
          :key="item.id"
          class="history-item"
          :class="{ active: currentDialogue === item.id }"
          @click="selectDialogue(item.id)"
        >
          <div class="history-icon">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M13.5 3H2.5C1.94772 3 1.5 3.44772 1.5 4V12C1.5 12.5523 1.94772 13 2.5 13H13.5C14.0523 13 14.5 12.5523 14.5 12V4C14.5 3.44772 14.0523 3 13.5 3Z" stroke="currentColor" stroke-width="1.5"/>
              <path d="M4.5 6H11.5M4.5 8.5H8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="history-content">
            <div class="history-title">{{ item.title }}</div>
            <div class="history-preview">{{ item.preview }}</div>
          </div>
          <div class="history-time">{{ formatTime(item.time) }}</div>
        </div>
      </div>
    </div>
    <div class="main">
      <div class="top">
        <button class="displaysidebar" @click="toggleSidebar" v-if="!isSidebarVisible">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 12L8 8L4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <button class="newdialogue" @click="createNewDialogue">
          <img src="/new_dialogue.svg" alt="新建对话" class="icon">
        </button>
        <div class="dialogue-title">{{ getCurrentDialogueTitle() }}</div>
      </div>
      <div class="dialogue" ref="dialogueContainer">
        <!-- 对话容器，限制最大宽度 -->
        <div class="dialogue-container">
          <div 
            v-for="message in currentMessages" 
            :key="message.id"
            class="message"
            :class="message.type"
          >
            <div class="avatar" v-if="message.type === 'user'">
              <div>您</div>
            </div>
            <div class="content" :class="message.type">
              <div v-if="message.type === 'user'">{{ message.content }}</div>
              <div v-else-if="message.type === 'draft'" class="draft-content">
                <div class="draft-header">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <span>采访报告</span>
                </div>
                <div class="markdown-content" v-html="renderMarkdown(message.content)"></div>
              </div>
              <div v-else class="markdown-content" v-html="renderMarkdown(message.content)"></div>
            </div>
          </div>
          <!-- AI回复时的加载指示器 -->
          <div v-if="isWaitingForAI" class="message assistant">
            <div class="content assistant loading">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
        <!-- 空状态提示 - 移动到对话区域内部，但独立于对话容器 -->
        <div v-if="currentMessages.length === 0 && !isWaitingForAI" class="empty-state">
          <div class="empty-content">
            <div class="empty-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                <path d="M8 12H8.01M12 12H12.01M16 12H16.01M21 12C21 16.418 16.97 20 12 20C10.46 20 9.01 19.59 7.75 18.87L3 20L4.13 15.25C3.41 13.99 3 12.54 3 11C3 6.582 7.03 3 12 3C16.97 3 21 6.582 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="empty-text">AI记者助手</div>
            <div class="empty-hint">请输入人物简介开始采访对话</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 错误提示 -->
    <div v-if="errorMessage" class="error-toast">
      {{ errorMessage }}
    </div>
    
    <!-- 输入框现在放在遮罩层后面 -->
    <div class="inputbox" :style="{ height: inputBoxHeight + 'px' }">
      <textarea 
        name="input" 
        :placeholder="isCurrentDialogueFinished ? '此对话已完成' : '请输入文字...'" 
        v-model="inputText"
        @keydown.enter.exact.prevent="sendMessage"
        @keydown.enter.shift.exact.prevent="inputText += '\n'"
        :disabled="isWaitingForAI || isCurrentDialogueFinished"
        ref="inputTextarea"
        @input="autoResizeTextarea"
        rows="1"
      ></textarea>
      <button @click="sendMessage" :disabled="!inputText.trim() || isWaitingForAI || isCurrentDialogueFinished">
        <img v-if="!isWaitingForAI" src="/send.svg" alt="发送" class="icon">
        <div v-else class="loading-spinner"></div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, nextTick, watch } from 'vue';

// 状态管理
const isSidebarVisible = ref(true);
const currentDialogue = ref(1);
const inputText = ref('');
const isWaitingForAI = ref(false); // 新增：等待AI回复状态
const inputBoxHeight = ref(80); // 输入框初始高度

// 获取DOM元素引用
const dialogueContainer = ref(null);
const inputTextarea = ref(null);

// API配置
const API_BASE_URL = '/api';

// 对话历史数据
const history = reactive([]);

// 消息数据
const messages = reactive({});

// 当前会话session_id
const currentSessionId = ref(null);

// 错误提示
const errorMessage = ref('');

const currentMessages = computed(() => {
  return messages[currentDialogue.value] || [];
});

const isCurrentDialogueFinished = computed(() => {
  const item = history.find(item => item.id === currentDialogue.value);
  return item ? item.is_finished : false;
});

// API调用函数
// 获取所有对话会话
const fetchDialogues = async () => {
  try {
    console.log('正在获取对话列表...', API_BASE_URL);
    const response = await fetch(`${API_BASE_URL}/dialogues`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('获取到的对话数据:', data);
    
    // 转换后端数据格式为前端需要的格式
    history.splice(0); // 清空现有数据
    Object.values(data).forEach(dialogue => {
      // 安全地处理QAs数组
      const qas = Array.isArray(dialogue.qas) ? dialogue.qas : [];
      const lastQA = qas.length > 0 ? qas[qas.length - 1] : null;
      
      // 生成预览和标题
      let preview = '对话尚未开始...';
      let title = '新对话';
      
      // 查找最后一个有答案的QA用作预览
      const lastAnsweredQA = qas.slice().reverse().find(qa => qa && qa.answer && qa.answer.trim());
      
      if (lastAnsweredQA) {
        preview = lastAnsweredQA.answer.length > 30 ? 
          lastAnsweredQA.answer.substring(0, 30) + '...' : lastAnsweredQA.answer;
      } else if (lastQA && lastQA.question) {
        // 如果没有答案但有问题，显示最新的问题
        preview = lastQA.question.length > 30 ? 
          lastQA.question.substring(0, 30) + '...' : lastQA.question;
      } else if (dialogue.draft && dialogue.draft.trim()) {
        preview = dialogue.draft.length > 30 ? dialogue.draft.substring(0, 30) + '...' : dialogue.draft;
      }
      
      // 标题使用第一个QA的问题或者最后一个QA的问题
      if (qas.length > 0 && qas[0].question) {
        title = qas[0].question.length > 15 ? 
          qas[0].question.substring(0, 15) + '...' : qas[0].question;
      } else if (dialogue.draft && dialogue.draft.trim()) {
        title = dialogue.draft.length > 15 ? dialogue.draft.substring(0, 15) + '...' : dialogue.draft;
      } else {
        title = `对话 ${dialogue.id}`;
      }
      
      history.push({
        id: dialogue.id,
        title,
        preview,
        time: dialogue.updated_at,
        is_finished: dialogue.is_finished || false
      });
      
      // 构建消息列表
      messages[dialogue.id] = [];
      qas.forEach((qa, index) => {
        if (qa && qa.question) {
          // 构建AI回复内容
          let aiContent = '';
          
          // 对于第一个QA，只显示aim和question
          if (index === 0) {
            // 添加意图信息
            if (qa.aim && qa.aim.trim()) {
              aiContent += `**目标:** ${qa.aim}\n\n`;
            }
            // 添加问题 - 使用特殊格式突出显示
            aiContent += `<div class="question-highlight">${qa.question}</div>`;
            console.log('Generated aiContent:', aiContent);
          } else {
            // 对于后续QA，显示上一轮的反馈信息（emotion、progress）+ 当前轮的aim、question
            const prevQA = qas[index - 1];
            
            // 添加上一轮的情绪反馈
            if (prevQA && prevQA.emotion && prevQA.emotion.trim()) {
              const emotionMap = {
                'positive': '😊 积极',
                'negative': '😔 消极',
                'neutral': '😐 中性',
                'excited': '🎉 兴奋',
                'sad': '😢 悲伤',
                'angry': '😠 愤怒',
                'surprised': '😲 惊讶'
              };
              const emotionText = emotionMap[prevQA.emotion] || prevQA.emotion;
              aiContent += `**检测情绪:** ${emotionText}\n\n`;
            }
            
            // 添加上一轮的进度信息
            if (prevQA && prevQA.progress && prevQA.progress.trim()) {
              aiContent += `**当前进度:** ${prevQA.progress}\n\n`;
            }
            
            // 添加当前轮的意图信息
            if (qa.aim && qa.aim.trim()) {
              aiContent += `**目标:** ${qa.aim}\n\n`;
            }
            
            // 添加当前轮的问题 - 使用特殊格式突出显示
            aiContent += `<div class="question-highlight">${qa.question}</div>`;
          }
          
          // 添加AI的回复
          messages[dialogue.id].push({
            id: qa.id * 2 - 1,
            type: 'assistant',
            content: aiContent
          });
          
          // 只有在有答案时才添加用户的回答
          if (qa.answer && qa.answer.trim()) {
            messages[dialogue.id].push({
              id: qa.id * 2,
              type: 'user',
              content: qa.answer
            });
          }
        }
      });
      
      // 如果对话已完成且有draft，添加draft作为最后一条消息
      if (dialogue.is_finished && dialogue.draft && dialogue.draft.trim()) {
        messages[dialogue.id].push({
          id: 'draft-' + dialogue.id,
          type: 'draft',
          content: dialogue.draft
        });
      }
    });
    
    // 按更新时间排序
    history.sort((a, b) => new Date(b.time) - new Date(a.time));
    console.log('处理后的历史数据:', history);
  } catch (error) {
    console.error('获取对话列表失败:', error);
    
    let errorMsg = '获取对话列表失败';
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      errorMsg += '：无法连接到后端服务，请确认后端服务运行在 http://localhost:5000';
    } else if (error.message.includes('CORS')) {
      errorMsg += '：跨域请求被阻止，请检查后端CORS配置';
    } else {
      errorMsg += `：${error.message}`;
    }
    
    errorMessage.value = errorMsg;
    setTimeout(() => {
      errorMessage.value = '';
    }, 8000);
  }
};

// 开始新对话
const startNewDialogue = async (input) => {
  try {
    isWaitingForAI.value = true;
    let isInterviewFinished = false;
    let finishMessageId = null;
    let sessionId = null;
    
    const response = await fetch(`${API_BASE_URL}/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({ input })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonData = JSON.parse(line.slice(6));
            console.log('StartNewDialogue - 收到数据:', jsonData);
            
            // 处理错误
            if (jsonData.type === 'error') {
              console.error('StartNewDialogue - 收到错误:', jsonData.content);
              errorMessage.value = jsonData.content || '开始新对话时发生错误';
              setTimeout(() => {
                errorMessage.value = '';
              }, 5000);
              return; // 退出处理
            }
            
            // 处理采访结束标志
            if (jsonData.type === 'is_finished' && (jsonData.data === 1 || jsonData.data === '1' || jsonData.content === '1')) {
              console.log('StartNewDialogue - 收到is_finished信号:', jsonData);
              isInterviewFinished = true;
              
              // 如果还没有sessionId，先从响应中获取
              if (!sessionId && jsonData.session_id) {
                sessionId = jsonData.session_id;
                currentSessionId.value = sessionId;
                console.log('StartNewDialogue - 从is_finished响应中获取sessionId:', sessionId);
              }
              
              // 确保sessionId已设置并初始化messages
              if (sessionId) {
                if (!messages[sessionId]) {
                  messages[sessionId] = [];
                }
                
                // 显示采访结束提示
                const finishMessage = {
                  id: Date.now(),
                  type: 'assistant',
                  content: '<div class="interview-finished-notice">🎉 **采访已完成！**<br><br>正在生成采访报告，请稍候...</div>'
                };
                
                console.log('StartNewDialogue - 添加采访结束提示消息:', finishMessage);
                messages[sessionId].push(finishMessage);
                finishMessageId = finishMessage.id;
                console.log('StartNewDialogue - messages数组当前内容:', messages[sessionId]);
                
                // 强制Vue响应式更新
                nextTick(() => {
                  console.log('StartNewDialogue - 强制更新后的currentMessages:', currentMessages.value);
                });
                
                // 更新对话状态为已完成
                const dialogueItem = history.find(item => item.id === sessionId);
                if (dialogueItem) {
                  dialogueItem.is_finished = true;
                  dialogueItem.time = new Date().toISOString();
                }
                
                // 自动滚动到底部
                nextTick(() => {
                  scrollToBottom();
                });
              }
              
              continue;
            }
            
            // 处理draft数据
            if (jsonData.type === 'draft' && jsonData.content && isInterviewFinished && sessionId) {
              console.log('StartNewDialogue - 收到draft数据:', jsonData);
              
              // 移除采访结束提示消息
              if (finishMessageId) {
                const messageIndex = messages[sessionId].findIndex(msg => msg.id === finishMessageId);
                console.log('StartNewDialogue - 移除提示消息，索引:', messageIndex);
                if (messageIndex !== -1) {
                  messages[sessionId].splice(messageIndex, 1);
                }
              }
              
              // 添加draft消息
              const draftMessage = {
                id: 'draft-' + sessionId,
                type: 'draft',
                content: jsonData.content
              };
              console.log('StartNewDialogue - 添加draft消息:', draftMessage);
              messages[sessionId].push(draftMessage);
              console.log('StartNewDialogue - messages数组最终内容:', messages[sessionId]);
              
              // 强制Vue响应式更新
              nextTick(() => {
                console.log('StartNewDialogue - Draft更新后的currentMessages:', currentMessages.value);
                scrollToBottom();
              });
              
              break;
            }
            
            // 处理正常的对话开始回复
            if (jsonData.type === 'final' && jsonData.data && !isInterviewFinished) {
              // 从响应数据中获取session_id，尝试多个可能的位置
              sessionId = jsonData.session_id || jsonData.data.session_id || jsonData.data.id;
              
              // 如果没有获取到session_id，记录警告并使用时间戳
              if (!sessionId) {
                console.warn('StartNewDialogue - 无法从响应中获取session_id，使用时间戳作为临时ID');
                sessionId = Date.now();
              }
              
              console.log('StartNewDialogue - 获取到session_id:', sessionId, '来源:', jsonData);
              currentSessionId.value = sessionId;
              
              // 添加用户输入到消息列表
              if (!messages[sessionId]) {
                messages[sessionId] = [];
              }
              
              messages[sessionId].push({
                id: Date.now() - 1,
                type: 'user',
                content: input
              });
              
              // 构建AI回复内容
              let aiContent = '';
              const data = jsonData.data;
              
              // 添加情绪反馈（对用户输入的反馈）
              if (data.emotion && data.emotion.trim()) {
                const emotionMap = {
                  'positive': '😊 积极',
                  'negative': '😔 消极',  
                  'neutral': '😐 中性',
                  'excited': '🎉 兴奋',
                  'sad': '😢 悲伤',
                  'angry': '😠 愤怒',
                  'surprised': '😲 惊讶'
                };
                const emotionText = emotionMap[data.emotion] || data.emotion;
                aiContent += `**检测情绪:** ${emotionText}\n\n`;
              }
              
              // 添加进度信息
              if (data.process && data.process.trim()) {
                aiContent += `**当前进度:** ${data.process}\n\n`;
              }
              
              // 添加意图信息
              if (data.aim && data.aim.trim()) {
                aiContent += `**目标:** ${data.aim}\n\n`;
              }
              
              // 添加问题 - 使用特殊格式突出显示
              if (data.question && data.question.trim()) {
                aiContent += `<div class="question-highlight">${data.question}</div>`;
                console.log('StartNewDialogue - Generated aiContent:', aiContent);
              }
              
              // 添加AI的完整回复
              messages[sessionId].push({
                id: Date.now(),
                type: 'assistant',
                content: aiContent
              });
              
              // 更新对话列表
              const newDialogue = {
                id: sessionId,
                title: data.question && data.question.length > 15 ? 
                  data.question.substring(0, 15) + '...' : 
                  (data.question || `对话 ${sessionId}`),
                preview: input.length > 30 ? input.substring(0, 30) + '...' : input,
                time: new Date().toISOString(),
                is_finished: false
              };
              
              history.unshift(newDialogue);
              currentDialogue.value = sessionId;
              console.log('StartNewDialogue - 新对话创建完成, sessionId:', sessionId, 'currentDialogue:', currentDialogue.value, 'currentSessionId:', currentSessionId.value);
              
              // 如果使用的是临时ID（时间戳），需要从后端获取真实的session_id
              if (!jsonData.session_id && !jsonData.data.session_id && !jsonData.data.id) {
                console.log('StartNewDialogue - 未获取到后端session_id，将在流结束后重新获取');
                // 标记需要在流结束后获取真实ID
                window.__needFetchRealSessionId = true;
                window.__tempSessionId = sessionId;
              }
              
              break;
            }
          } catch (e) {
            console.error('解析流式响应失败:', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('开始新对话失败:', error);
    errorMessage.value = '开始新对话失败，请检查后端服务是否正常运行';
    setTimeout(() => {
      errorMessage.value = '';
    }, 5000);
  } finally {
    isWaitingForAI.value = false;
    
    // 如果标记了需要获取真实session_id，现在获取
    if (window.__needFetchRealSessionId && window.__tempSessionId) {
      console.log('StartNewDialogue - 流处理完成，开始获取真实session_id');
      const tempId = window.__tempSessionId;
      
      try {
        // 短暂延迟，确保后端已保存会话
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // 获取最新的对话列表
        const response = await fetch(`${API_BASE_URL}/dialogues`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          const dialogues = Object.values(data);
          
          // 找到最新创建的对话（按created_at排序）
          if (dialogues.length > 0) {
            const sortedDialogues = dialogues.sort((a, b) => 
              new Date(b.created_at) - new Date(a.created_at)
            );
            const latestDialogue = sortedDialogues[0];
            const realSessionId = latestDialogue.id;
            
            console.log('StartNewDialogue - 获取到真实session_id:', realSessionId, '临时ID:', tempId);
            
            // 更新所有相关状态
            if (messages[tempId]) {
              messages[realSessionId] = messages[tempId];
              delete messages[tempId];
            }
            
            // 更新history中的ID
            const historyItem = history.find(item => item.id === tempId);
            if (historyItem) {
              historyItem.id = realSessionId;
            }
            
            // 更新当前会话ID
            if (currentDialogue.value === tempId) {
              currentDialogue.value = realSessionId;
            }
            if (currentSessionId.value === tempId) {
              currentSessionId.value = realSessionId;
            }
            
            console.log('StartNewDialogue - session_id更新完成:', {
              old: tempId,
              new: realSessionId,
              currentDialogue: currentDialogue.value,
              currentSessionId: currentSessionId.value
            });
          }
        }
      } catch (error) {
        console.error('StartNewDialogue - 获取真实session_id失败:', error);
      } finally {
        delete window.__needFetchRealSessionId;
        delete window.__tempSessionId;
      }
    }
  }
};

// 继续对话
const continueDialogue = async (sessionId, input) => {
  try {
    isWaitingForAI.value = true;
    let isInterviewFinished = false;
    let finishMessageId = null;
    
    const response = await fetch(`${API_BASE_URL}/continue`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({ session_id: sessionId, input })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonData = JSON.parse(line.slice(6));
            console.log('ContinueDialogue - 收到数据:', jsonData);
            
            // 处理错误
            if (jsonData.type === 'error') {
              console.error('ContinueDialogue - 收到错误:', jsonData.content);
              errorMessage.value = jsonData.content || '继续对话时发生错误';
              setTimeout(() => {
                errorMessage.value = '';
              }, 5000);
              return; // 退出处理
            }
            
            // 处理采访结束标志
            if (jsonData.type === 'is_finished' && (jsonData.data === 1 || jsonData.data === '1' || jsonData.content === '1')) {
              console.log('收到is_finished信号:', jsonData);
              isInterviewFinished = true;
              
              // 确保messages数组已初始化
              if (!messages[sessionId]) {
                messages[sessionId] = [];
              }
              
              // 显示采访结束提示
              const finishMessage = {
                id: Date.now(),
                type: 'assistant',
                content: '<div class="interview-finished-notice">🎉 采访已完成！<br><br>正在生成采访报告，请稍候...</div>'
              };
              
              console.log('添加采访结束提示消息:', finishMessage);
              messages[sessionId].push(finishMessage);
              finishMessageId = finishMessage.id;
              console.log('ContinueDialogue - messages数组当前内容:', messages[sessionId]);
              
              // 强制Vue响应式更新
              // 更新对话状态为已完成
              const dialogueItem = history.find(item => item.id === sessionId);
              if (dialogueItem) {
                dialogueItem.is_finished = true;
                dialogueItem.time = new Date().toISOString();
              }
              
              // 自动滚动到底部
              nextTick(() => {
                console.log('ContinueDialogue - Finish更新后的currentMessages:', currentMessages.value);
                scrollToBottom();
              });
              
              continue;
            }
            
            // 处理draft数据
            if (jsonData.type === 'draft' && jsonData.content && isInterviewFinished && sessionId) {
              console.log('ContinueDialogue - 收到draft数据:', jsonData);
              
              // 移除采访结束提示消息
              if (finishMessageId) {
                const messageIndex = messages[sessionId].findIndex(msg => msg.id === finishMessageId);
                console.log('ContinueDialogue - 移除提示消息，索引:', messageIndex);
                if (messageIndex !== -1) {
                  messages[sessionId].splice(messageIndex, 1);
                }
              }
              
              // 添加draft消息
              const draftMessage = {
                id: 'draft-' + sessionId,
                type: 'draft',
                content: jsonData.content
              };
              console.log('ContinueDialogue - 添加draft消息:', draftMessage);
              messages[sessionId].push(draftMessage);
              console.log('ContinueDialogue - messages数组最终内容:', messages[sessionId]);
              
              // 强制Vue响应式更新
              nextTick(() => {
                console.log('ContinueDialogue - Draft更新后的currentMessages:', currentMessages.value);
                scrollToBottom();
              });
              nextTick(() => {
                scrollToBottom();
              });
              
              break;
            }
            
            // 处理正常的对话回复
            if (jsonData.type === 'final' && jsonData.data && !isInterviewFinished) {
              // 构建AI回复内容（继续对话时显示反馈信息 + 新问题）
              let aiContent = '';
              const data = jsonData.data;
              
              // 添加情绪反馈（对用户刚才回答的反馈）
              if (data.emotion && data.emotion.trim()) {
                const emotionMap = {
                  'positive': '😊 积极',
                  'negative': '😔 消极',
                  'neutral': '😐 中性',
                  'excited': '🎉 兴奋',
                  'sad': '😢 悲伤',
                  'angry': '😠 愤怒',
                  'surprised': '😲 惊讶'
                };
                const emotionText = emotionMap[data.emotion] || data.emotion;
                aiContent += `**检测情绪:** ${emotionText}\n\n`;
              }
              
              // 添加进度信息
              if (data.process && data.process.trim()) {
                aiContent += `**当前进度:** ${data.process}\n\n`;
              }
              
              // 添加意图信息
              if (data.aim && data.aim.trim()) {
                aiContent += `**目标:** ${data.aim}\n\n`;
              }
              
              // 添加问题 - 使用特殊格式突出显示
              if (data.question && data.question.trim()) {
                aiContent += `<div class="question-highlight">${data.question}</div>`;
                console.log('ContinueDialogue - Generated aiContent:', aiContent);
              }
              
              // 添加AI的完整回复
              messages[sessionId].push({
                id: Date.now(),
                type: 'assistant',
                content: aiContent
              });
              
              // 更新对话时间（预览保持为用户的最新回答）
              const dialogueItem = history.find(item => item.id === sessionId);
              if (dialogueItem) {
                dialogueItem.time = new Date().toISOString();
              }
              break;
            }
          } catch (e) {
            console.error('解析流式响应失败:', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('继续对话失败:', error);
    errorMessage.value = '继续对话失败，请检查后端服务是否正常运行';
    setTimeout(() => {
      errorMessage.value = '';
    }, 5000);
  } finally {
    isWaitingForAI.value = false;
  }
};

// 简单的Markdown解析函数
const renderMarkdown = (text) => {
  if (!text) return '';
  
  // 确保 text 是字符串类型
  if (typeof text !== 'string') {
    console.warn('renderMarkdown received non-string:', typeof text, text);
    text = String(text);
  }
  
  // 先保护自定义HTML标签，避免被后续处理破坏
  const htmlPlaceholders = {};
  let placeholderIndex = 0;
  
  // 保护question-highlight标签
  text = text.replace(/<div class="question-highlight">(.*?)<\/div>/g, (match) => {
    const placeholder = `__HTML_PLACEHOLDER_${placeholderIndex}__`;
    htmlPlaceholders[placeholder] = match;
    placeholderIndex++;
    return placeholder;
  });
  
  // 保护interview-finished-notice标签
  text = text.replace(/<div class="interview-finished-notice">(.*?)<\/div>/g, (match) => {
    const placeholder = `__HTML_PLACEHOLDER_${placeholderIndex}__`;
    htmlPlaceholders[placeholder] = match;
    placeholderIndex++;
    return placeholder;
  });
  
  // 处理标题
  text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  text = text.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  text = text.replace(/^# (.*$)/gim, '<h1>$1</h1>');
  
  // 处理粗体
  text = text.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
  text = text.replace(/\*(.*?)\*/gim, '<em>$1</em>');
  
  // 处理代码块
  text = text.replace(/```([^`]+)```/gim, '<pre><code>$1</code></pre>');
  text = text.replace(/`([^`]+)`/gim, '<code>$1</code>');
  
  // 处理列表
  text = text.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
  text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  
  // 处理数字列表
  text = text.replace(/^\s*\d+\.\s+(.*$)/gim, '<li>$1</li>');
  text = text.replace(/(<li>.*<\/li>)/s, '<ol>$1</ol>');
  
  // 处理换行
  text = text.replace(/\n/g, '<br>');
  
  // 处理段落
  text = text.replace(/<br><br>/g, '</p><p>');
  text = '<p>' + text + '</p>';
  
  // 恢复自定义HTML标签
  Object.keys(htmlPlaceholders).forEach(placeholder => {
    text = text.replace(placeholder, htmlPlaceholders[placeholder]);
  });
  
  return text;
};

// 自动调整textarea高度
const autoResizeTextarea = () => {
  nextTick(() => {
    if (!inputTextarea.value) return;
    
    // 重置高度为auto以计算正确的高度
    inputTextarea.value.style.height = 'auto';
    
    // 计算新的高度
    const newHeight = Math.min(inputTextarea.value.scrollHeight, 200); // 最大高度200px
    
    // 设置textarea的高度
    inputTextarea.value.style.height = newHeight + 'px';
    
    // 更新输入框容器高度
    inputBoxHeight.value = Math.max(80, newHeight + 32); // 最小高度80px，加上内边距
  });
};

// 方法
const toggleSidebar = () => {
  isSidebarVisible.value = !isSidebarVisible.value;
};

const createNewDialogue = () => {
  // 清空当前对话相关状态
  currentDialogue.value = null;
  currentSessionId.value = null;
  inputText.value = '';
  isWaitingForAI.value = false;
  
  // 重置输入框高度并聚焦
  nextTick(() => {
    if (inputTextarea.value) {
      inputTextarea.value.style.height = 'auto';
      inputBoxHeight.value = 80;
      inputTextarea.value.focus();
    }
  });
};

const selectDialogue = (id) => {
  currentDialogue.value = id;
  currentSessionId.value = id;
  // 在选择对话后自动隐藏侧边栏
  isSidebarVisible.value = false;
  isWaitingForAI.value = false; // 重置等待状态
  
  // 自动滚动到对话底部
  nextTick(() => {
    scrollToBottom();
  });
};

const sendMessage = async () => {
  if (!inputText.value.trim() || isWaitingForAI.value || isCurrentDialogueFinished.value) return;
  
  const messageContent = inputText.value.trim();
  
  console.log('sendMessage - currentSessionId:', currentSessionId.value);
  console.log('sendMessage - currentDialogue:', currentDialogue.value);
  console.log('sendMessage - messageContent:', messageContent);
  
  // 如果是新对话（没有当前会话ID）
  if (!currentSessionId.value) {
    console.log('sendMessage - 开始新对话');
    // 开始新对话
    await startNewDialogue(messageContent);
  } else {
    console.log('sendMessage - 继续现有对话, sessionId:', currentSessionId.value);
    // 继续现有对话
    // 先添加用户消息到当前对话
    if (!messages[currentSessionId.value]) {
      messages[currentSessionId.value] = [];
    }
    
    messages[currentSessionId.value].push({
      id: Date.now(),
      type: 'user',
      content: messageContent
    });
    
    // 更新对话历史预览
    const currentHistoryItem = history.find(item => item.id === currentSessionId.value);
    if (currentHistoryItem) {
      const singleLinePreview = messageContent.replace(/\n/g, ' ');
      currentHistoryItem.preview = singleLinePreview.length > 30 
        ? singleLinePreview.substring(0, 30) + '...' 
        : singleLinePreview;
      currentHistoryItem.time = new Date().toISOString();
      
      // 将当前对话移动到历史列表顶部
      const index = history.indexOf(currentHistoryItem);
      if (index > 0) {
        history.splice(index, 1);
        history.unshift(currentHistoryItem);
      }
    }
    
    // 自动滚动到对话底部
    nextTick(() => {
      scrollToBottom();
    });
    
    // 继续对话
    await continueDialogue(currentSessionId.value, messageContent);
  }
  
  // 清空输入框并重置高度
  inputText.value = '';
  nextTick(() => {
    if (inputTextarea.value) {
      inputTextarea.value.style.height = 'auto';
      inputBoxHeight.value = 80;
    }
  });
};

// 滚动到对话底部
const scrollToBottom = () => {
  if (dialogueContainer.value) {
    dialogueContainer.value.scrollTop = dialogueContainer.value.scrollHeight;
  }
};

const getCurrentDialogueTitle = () => {
  const item = history.find(item => item.id === currentDialogue.value);
  return item ? item.title : 'AI记者助手';
};

const formatTime = (timeString) => {
  const time = new Date(timeString);
  const now = new Date();
  const diffInHours = (now - time) / (1000 * 60 * 60);
  
  if (diffInHours < 1) {
    return '刚刚';
  } else if (diffInHours < 24) {
    return `${Math.floor(diffInHours)}小时前`;
  } else {
    return `${Math.floor(diffInHours / 24)}天前`;
  }
};

// 监听当前对话变化，自动滚动到底部
watch(currentDialogue, () => {
  nextTick(() => {
    scrollToBottom();
  });
});

// 监听当前消息变化，自动滚动到底部
watch(currentMessages, () => {
  nextTick(() => {
    scrollToBottom();
  });
}, { deep: true });

// 监听输入文本变化，自动调整高度
watch(inputText, () => {
  autoResizeTextarea();
});

onMounted(async () => {
  // 加载历史对话数据
  await fetchDialogues();
  
  // 初始化第一个对话
  if (history.length > 0) {
    currentDialogue.value = history[0].id;
    currentSessionId.value = history[0].id;
  }
  
  // 测试问题高亮样式和采访结束流程
  if (history.length === 0) {
    // 添加一个测试消息来验证样式
    const testSessionId = 'test-123';
    messages[testSessionId] = [
      {
        id: 1,
        type: 'assistant',
        content: '**目标:** 测试问题高亮样式\n\n<div class="question-highlight">这是一个测试问题，用来验证问题高亮样式是否正常工作？</div>'
      },
      {
        id: 2,
        type: 'assistant', 
        content: '<div class="interview-finished-notice">🎉 **采访已完成！**<br><br>正在生成采访报告，请稍候...</div>'
      },
      {
        id: 'draft-test-123',
        type: 'draft',
        content: '# 测试采访报告\n\n这是一个测试的采访报告内容，用来验证draft消息是否能正确显示。\n\n## 主要内容\n- 测试项目1\n- 测试项目2\n- 测试项目3'
      }
    ];
    
    history.push({
      id: testSessionId,
      title: '样式测试',
      preview: '测试问题高亮样式和采访结束流程',
      time: new Date().toISOString(),
      is_finished: true
    });
    
    currentDialogue.value = testSessionId;
    currentSessionId.value = testSessionId;
    
    console.log('Added test messages with question highlight, interview finish, and draft');
  }
  
  // 自动聚焦到输入框
  nextTick(() => {
    if (inputTextarea.value) {
      inputTextarea.value.focus();
    }
  });
});
</script>

<style>
/* 全局样式重置 */
body {
  margin: 0;
  padding: 0;
  overflow: hidden;
  background-color: #1a1a1a;
  color: #e0e0e0;
}

#app {
  height: 100vh;
}

/* 问题突出显示样式 - 全局样式 */
.question-highlight {
  background: linear-gradient(135deg, #3a4a5c, #4a5568);
  color: #e2e8f0;
  padding: 16px 20px;
  border-radius: 12px;
  margin: 16px 0;
  font-weight: 600;
  font-size: 15px;
  line-height: 1.6;
  border-left: 4px solid #68d391;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  position: relative;
  overflow: hidden;
  border: 1px solid #4a5568;
}

.question-highlight::before {
  content: '🤔';
  font-size: 18px;
  margin-right: 8px;
  opacity: 0.9;
}

.question-highlight::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: linear-gradient(45deg, transparent 30%, rgba(104, 211, 145, 0.1) 50%, transparent 70%);
  pointer-events: none;
}

/* 采访结束提示样式 - 全局样式 */
.interview-finished-notice {
  background: linear-gradient(135deg, #4c51bf, #6366f1);
  color: #ffffff;
  padding: 20px 24px;
  border-radius: 16px;
  margin: 20px 0;
  font-weight: 600;
  font-size: 16px;
  line-height: 1.6;
  text-align: center;
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.3);
  position: relative;
  overflow: hidden;
  border: 2px solid #6366f1;
}

.interview-finished-notice::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
  pointer-events: none;
}
</style>

<style scoped>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.root {
  display: flex;
  height: 100vh;
  background-color: #1a1a1a;
  transition: all 0.3s ease;
  position: relative;
  color: #e0e0e0;
}

/* 侧边栏遮罩层 */
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  z-index: 20; /* 提高遮罩层的z-index */
}

/* 侧边栏样式 */
.sidebar {
  width: 260px;
  background-color: #2d2d2d;
  border-right: 1px solid #404040;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 30; /* 提高侧边栏的z-index，确保它在遮罩层之上 */
  transform: translateX(0);
}

.root.sidebar-hidden .sidebar {
  transform: translateX(-100%);
}

.sidebar .top {
  padding: 12px;
  border-bottom: 1px solid #404040;
  display: flex;
  gap: 8px;
}

.sidebar .top button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  border: 1px solid #555;
  border-radius: 6px;
  background: #3a3a3a;
  color: #e0e0e0;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  gap: 6px;
}

.sidebar .top button:hover {
  background: #4a4a4a;
  border-color: #666;
}

.sidebar .top .newdialogue {
  flex: 1;
}

.sidebar .top .hidesidebar {
  width: 36px;
  padding: 8px;
}

.list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.history-item {
  display: flex;
  padding: 12px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: all 0.2s;
  gap: 10px;
  position: relative;
}

.history-item:hover {
  background: #3a3a3a;
}

.history-item.active {
  background: #404040;
  border-left-color: #6d8cff;
}

.history-icon {
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
  color: #888;
}

.history-content {
  flex: 1;
  min-width: 0;
}

.history-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #e0e0e0;
}

.history-preview {
  font-size: 12px;
  color: #aaa;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-time {
  font-size: 11px;
  color: #777;
  white-space: nowrap;
}

/* 主区域样式 */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-left: 0;
  transition: margin-left 0.3s ease;
  background-color: #1a1a1a;
}

.root:not(.sidebar-hidden) .main {
  margin-left: 260px;
}

.main .top {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #404040;
  background: #2d2d2d;
  gap: 12px;
}

.main .top button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid #555;
  border-radius: 6px;
  background: #3a3a3a;
  color: #e0e0e0;
  cursor: pointer;
  transition: all 0.2s;
}

.main .top button:hover {
  background: #4a4a4a;
  border-color: #666;
}

.main .top .dialogue-title {
  font-size: 16px;
  font-weight: 600;
  flex: 1;
  text-align: center;
  color: #e0e0e0;
}

/* 对话区域样式 - 关键修改 */
.dialogue {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding-bottom: 130px; /* 为输入框留出空间 */
  background-color: #1a1a1a;
  width: 100%;
  position: relative; /* 为绝对定位的空状态提供参考 */
}

/* 对话容器 - 限制最大宽度并居中 */
.dialogue-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 800px; /* 限制对话区域最大宽度 */
  width: 100%;
  margin: 0 auto; /* 居中显示 */
}

.message {
  display: flex;
  gap: 12px;
  max-width: 100%;
}

.message.user {
  flex-direction: row-reverse;
}

/* AI消息 - 去掉头像和flex布局 */
.message.assistant {
  display: block; /* 改为块级元素，去掉flex布局 */
}

/* Draft消息样式 */
.message.draft {
  display: block;
  margin-top: 32px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}

.message.user .avatar {
  background: #6d8cff;
  color: white;
}

.content {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: pre-wrap; /* 保留换行符和空格 */
}

/* 用户消息样式保持不变 */
.message.user .content {
  background: #3a3a3a;
  color: #e0e0e0;
  border-top-right-radius: 4px;
  border: 1px solid #555;
  max-width: 70%; /* 用户消息保持原有最大宽度 */
}

/* AI消息样式 - 去掉气泡框，使用全宽度 */
.content.assistant {
  background: none;
  border: none;
  padding: 8px 0; /* 减少内边距 */
  border-radius: 0;
  max-width: 100%; /* AI回复使用全宽度 */
  color: #e0e0e0;
}

/* Draft消息样式 */
.content.draft {
  background: #2a2a2a;
  border: 2px solid #6d8cff;
  border-radius: 12px;
  padding: 24px;
  max-width: 100%;
  color: #e0e0e0;
}

.draft-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-weight: 600;
  font-size: 16px;
  color: #6d8cff;
}

.draft-content {
  width: 100%;
}

/* Markdown内容样式 */
.markdown-content {
  line-height: 1.6;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  margin: 1.2em 0 0.6em 0;
  color: #e0e0e0;
  font-weight: 600;
}

.markdown-content h1 {
  font-size: 1.5em;
  border-bottom: 1px solid #404040;
  padding-bottom: 0.3em;
}

.markdown-content h2 {
  font-size: 1.3em;
}

.markdown-content h3 {
  font-size: 1.1em;
}

.markdown-content p {
  margin: 1em 0;
}

.markdown-content ul,
.markdown-content ol {
  margin: 1em 0;
  padding-left: 2em;
}

.markdown-content li {
  margin: 0.5em 0;
}

.markdown-content strong {
  font-weight: 600;
  color: #ffffff;
}

.markdown-content em {
  font-style: italic;
}

.markdown-content code {
  background-color: #2d2d2d;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  color: #e0e0e0;
  border: 1px solid #404040;
}

.markdown-content pre {
  background-color: #2d2d2d;
  padding: 1em;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1em 0;
  border: 1px solid #404040;
}

.markdown-content pre code {
  background: none;
  padding: 0;
  border: none;
  color: #e0e0e0;
}

/* 空状态样式 - 修改为窗口中央显示 */
.empty-state {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  max-width: 400px;
  padding: 40px;
}

.empty-icon {
  margin-bottom: 24px;
  color: #666;
}

.empty-text {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #e0e0e0;
}

.empty-hint {
  font-size: 14px;
  color: #888;
  line-height: 1.5;
}

/* 输入框样式 - 降低z-index */
.inputbox {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: #2d2d2d;
  border-top: 1px solid #404040;
  display: flex;
  gap: 12px;
  align-items: center;
  z-index: 10; /* 降低输入框的z-index，使其在遮罩层之下 */
  transition: all 0.3s ease;
  margin: 16px;
  border-radius: 20px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.2);
  min-height: 80px; /* 最小高度 */
  height: auto; /* 高度自适应 */
  overflow: hidden; /* 防止内容溢出 */
}

.root:not(.sidebar-hidden) .inputbox {
  left: 260px;
}

.inputbox textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #555;
  border-radius: 24px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  outline: none;
  max-height: 200px; /* 最大高度限制 */
  min-height: 44px;
  height: auto; /* 高度自适应 */
  transition: all 0.2s;
  background: #3a3a3a;
  color: #e0e0e0;
  overflow-y: auto; /* 内容过多时显示滚动条 */
  white-space: pre-wrap; /* 保留换行符和空格 */
}

.inputbox textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.inputbox textarea::placeholder {
  color: #888;
}

.inputbox textarea:focus {
  border-color: #6d8cff;
  box-shadow: 0 0 0 2px rgba(109, 140, 255, 0.2);
}

.inputbox button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  background: #6d8cff;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.inputbox button:hover:not(:disabled) {
  background: #5a7dff;
  transform: scale(1.05);
}

.inputbox button:disabled {
  background: #555;
  cursor: not-allowed;
  transform: none;
}

/* 图标样式 */
.icon {
  width: 16px;
  height: 16px;
  display: inline-block;
  filter: invert(0.8); /* 使图标在暗色背景下更清晰 */
}

/* 显示侧边栏按钮在所有设备上都显示 */
.main .top .displaysidebar {
  display: flex;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .root:not(.sidebar-hidden) .main {
    margin-left: 0;
  }
  
  .root:not(.sidebar-hidden) .inputbox {
    left: 0;
  }
  
  .message.user .content {
    max-width: 85%;
  }
  
  .inputbox {
    padding: 12px;
    margin: 12px;
    min-height: 76px; /* 移动端最小高度稍小 */
  }
  
  .inputbox textarea {
    min-height: 40px;
    font-size: 16px; /* 移动端更好的输入体验 */
  }
  
  /* 移动端对话容器调整 */
  .dialogue-container {
    max-width: 100%;
  }
  
  /* 移动端空状态调整 */
  .empty-content {
    padding: 20px;
  }
  
  .empty-text {
    font-size: 18px;
  }
  
  /* 移动端Markdown样式调整 */
  .markdown-content h1 {
    font-size: 1.3em;
  }
  
  .markdown-content h2 {
    font-size: 1.2em;
  }
  
  .markdown-content h3 {
    font-size: 1.1em;
  }
  
  .markdown-content pre {
    padding: 0.8em;
    font-size: 0.9em;
  }
}

/* 中等屏幕适配 */
@media (min-width: 769px) and (max-width: 1200px) {
  .dialogue-container {
    max-width: 700px;
  }
}

/* 大屏幕适配 */
@media (min-width: 1201px) {
  .dialogue-container {
    max-width: 800px;
  }
  
  .inputbox {
    max-width: 800px;
    margin: 16px auto;
    left: 50%;
    transform: translateX(-50%);
  }
  
  .root:not(.sidebar-hidden) .inputbox {
    left: calc(50% + 130px); /* 考虑侧边栏宽度的一半 */
  }
}

/* 超大屏幕适配 */
@media (min-width: 1600px) {
  .dialogue-container {
    max-width: 900px;
  }
  
  .inputbox {
    max-width: 900px;
  }
}

/* 滚动条样式 */
.list::-webkit-scrollbar,
.dialogue::-webkit-scrollbar {
  width: 6px;
}

.list::-webkit-scrollbar-track,
.dialogue::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.list::-webkit-scrollbar-thumb,
.dialogue::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 3px;
}

.list::-webkit-scrollbar-thumb:hover,
.dialogue::-webkit-scrollbar-thumb:hover {
  background: #666;
}

/* 滚动条火狐浏览器兼容 */
.list, .dialogue {
  scrollbar-width: thin;
  scrollbar-color: #555 #2d2d2d;
}

/* AI回复加载指示器样式 */
.loading {
  display: flex;
  align-items: center;
  min-height: 40px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  background-color: #aaa;
  border-radius: 50%;
  display: inline-block;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 发送按钮加载动画 */
.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误提示样式 */
.error-toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #ff4444;
  color: white;
  padding: 12px 24px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  font-size: 14px;
  max-width: 400px;
  text-align: center;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

</style>