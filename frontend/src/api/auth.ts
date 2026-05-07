import request from './request'
import type { AxiosPromise } from 'axios'

export interface LoginForm {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserInfo {
  id: number
  username: string
  email?: string
  full_name?: string
  is_active: boolean
  created_at: string
}

export function login(data: LoginForm): AxiosPromise<TokenResponse> {
  const formData = new FormData()
  formData.append('username', data.username)
  formData.append('password', data.password)
  return request({
    url: '/api/v1/auth/login',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function refreshToken(refresh_token: string): AxiosPromise<TokenResponse> {
  return request({
    url: '/api/v1/auth/refresh',
    method: 'post',
    params: { refresh_token }
  })
}

export function logout(): AxiosPromise<any> {
  return request({
    url: '/api/v1/auth/logout',
    method: 'post'
  })
}

export function getUserInfo(): AxiosPromise<UserInfo> {
  return request({
    url: '/api/v1/auth/me',
    method: 'get'
  })
}
