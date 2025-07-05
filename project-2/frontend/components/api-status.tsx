"use client"

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

export function ApiStatus() {
  const [status, setStatus] = useState<'loading' | 'connected' | 'error'>('loading')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await apiClient.healthCheck()
        if (response.success) {
          setStatus('connected')
          setError(null)
        } else {
          setStatus('error')
          setError(response.error || 'Unknown error')
        }
      } catch (err) {
        setStatus('error')
        setError(err instanceof Error ? err.message : 'Connection failed')
      }
    }

    checkConnection()
  }, [])

  if (status === 'loading') {
    return (
      <div className="flex items-center text-sm text-gray-500">
        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        Checking API connection...
      </div>
    )
  }

  if (status === 'connected') {
    return (
      <div className="flex items-center text-sm text-green-600">
        <CheckCircle className="h-4 w-4 mr-2" />
        Connected to API
      </div>
    )
  }

  return (
    <div className="flex items-center text-sm text-red-600">
      <XCircle className="h-4 w-4 mr-2" />
      API Connection Error: {error}
    </div>
  )
} 