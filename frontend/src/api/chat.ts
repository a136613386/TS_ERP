import request from './request'

export interface ChatQueryRequest {
  message: string
  session_id?: string
}

export interface ChatResponse {
  answer: string
  sql?: string
  citations?: any[]
  data?: any
  intent: string
  session_id: string
}

export function chatQuery(data: ChatQueryRequest): Promise<ChatResponse> {
  return request({
    url: '/api/v1/chat/query',
    method: 'post',
    data
  })
}

export function resetChatSession(session_id: string): Promise<any> {
  return request({
    url: '/api/v1/chat/reset',
    method: 'post',
    params: { session_id }
  })
}

export function getChatHistory(session_id: string, limit = 20): Promise<any[]> {
  return request({
    url: '/api/v1/chat/history',
    method: 'get',
    params: { session_id, limit }
  })
}
