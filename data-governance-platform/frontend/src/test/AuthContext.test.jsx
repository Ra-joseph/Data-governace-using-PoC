/**
 * Unit tests for AuthContext
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import React from 'react'
import { AuthProvider, useAuth } from '../contexts/AuthContext'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
    get _store() { return store },
  }
})()

Object.defineProperty(window, 'localStorage', { value: localStorageMock })

const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>

describe('AuthContext', () => {
  beforeEach(() => {
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  it('should throw error when useAuth is used outside AuthProvider', () => {
    // Suppress console.error for this expected error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => {
      renderHook(() => useAuth())
    }).toThrow('useAuth must be used within an AuthProvider')
    spy.mockRestore()
  })

  it('should have null user initially when nothing stored', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.loading).toBe(false)
  })

  it('should load stored user from localStorage on mount', () => {
    const storedUser = { id: 1, name: 'Test User', role: 'admin' }
    localStorageMock.setItem('user', JSON.stringify(storedUser))

    const { result } = renderHook(() => useAuth(), { wrapper })

    // After mount + useEffect, user should be loaded
    expect(result.current.user).toEqual(storedUser)
    expect(result.current.isAuthenticated).toBe(true)
  })

  it('should login and set user + localStorage', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    const userData = { id: 1, name: 'New User', role: 'data_owner', token: 'abc123' }

    act(() => {
      result.current.login(userData)
    })

    expect(result.current.user).toEqual(userData)
    expect(result.current.isAuthenticated).toBe(true)
    expect(localStorageMock.setItem).toHaveBeenCalledWith('user', JSON.stringify(userData))
    expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'abc123')
  })

  it('should login without token', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    const userData = { id: 1, name: 'No Token User', role: 'consumer' }

    act(() => {
      result.current.login(userData)
    })

    expect(result.current.user).toEqual(userData)
    expect(localStorageMock.setItem).toHaveBeenCalledWith('user', JSON.stringify(userData))
    // auth_token should not be set when no token provided
    expect(localStorageMock.setItem).not.toHaveBeenCalledWith('auth_token', expect.anything())
  })

  it('should logout and clear state + localStorage', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    act(() => {
      result.current.login({ id: 1, name: 'User', role: 'admin', token: 'xyz' })
    })
    expect(result.current.isAuthenticated).toBe(true)

    act(() => {
      result.current.logout()
    })

    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('user')
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token')
  })

  it('should return true for hasRole when role matches', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    act(() => {
      result.current.login({ id: 1, name: 'Admin', role: 'admin' })
    })

    expect(result.current.hasRole('admin')).toBe(true)
  })

  it('should return false for hasRole when role does not match', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    act(() => {
      result.current.login({ id: 1, name: 'Consumer', role: 'data_consumer' })
    })

    expect(result.current.hasRole('admin')).toBe(false)
  })

  it('should return false for hasRole when no user is logged in', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.hasRole('admin')).toBe(false)
  })

  it('should report isAuthenticated true when user is present', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    act(() => {
      result.current.login({ id: 1, name: 'User', role: 'steward' })
    })

    expect(result.current.isAuthenticated).toBe(true)
  })

  it('should report isAuthenticated false when no user', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.isAuthenticated).toBe(false)
  })
})
