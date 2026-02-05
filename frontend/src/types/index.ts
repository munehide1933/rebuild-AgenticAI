export interface Conversation {
  id: string;
  title?: string;
  created_at?: string;
  updated_at?: string;
  messages?: Message[];
}

export interface Message {
  id: string | number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  meta_info?: MessageMetaInfo;
  created_at: string;
}

// ✨ 新增：完整的元信息类型
export interface MessageMetaInfo {
  // 推理相关
  strategy?: 'cot' | 'react' | 'direct';
  model?: 'gpt-4o' | 'deepseek-r1';
  confidence?: number;
  
  // CoT 推理轨迹
  reasoning_trace?: string[];
  
  // ReAct 步骤
  react_steps?: ReactStep[];
  
  // 工作流相关（兼容旧版）
  workflow_phase?: string;
  
  // 代码相关
  code_modifications?: CodeModification[];
  
  // 安全提示
  security_warnings?: string[];
  
  // Token 使用情况
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

// ✨ 新增：ReAct 步骤详情
export interface ReactStep {
  step: number;
  action: string;
  input: string;
  output: string;
}

export interface CodeModification {
  file_path: string;
  modification_type: 'ADD' | 'MODIFY' | 'DELETE';
  content: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  message_id: string;
  content: string;
  conversation_id: string;
  workflow_state?: {
    current_phase: string;
    active_personas: string[];
    phase_outputs?: Record<string, any>;
    security_flags?: string[];
  };
  code_modifications?: CodeModification[];
  suggestions?: string[];
}
