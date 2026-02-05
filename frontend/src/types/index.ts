export interface Conversation {
  id: string;
  title: string;
  summary: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface Message {
  id: string | number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  meta_info?: MessageMetaInfo;
  created_at: string;
}

export interface MessageMetaInfo {
  strategy?: 'cot' | 'react' | 'direct';
  model?: 'gpt5' | 'DeepSeek-R1-0528' | string;
  confidence?: number;
  reasoning_trace?: string[];
  react_steps?: ReactStep[];
  workflow_phase?: string;
  code_modifications?: CodeModification[];
  security_warnings?: string[];
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  mcp?: Record<string, unknown>;
}

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

export interface ConversationDetail extends Conversation {
  messages: Message[];
}
