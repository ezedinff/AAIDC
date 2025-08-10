import { useState, useEffect, useCallback } from 'react'
import { apiClient, Video } from '../api'

export interface VideoLibraryState {
  videos: Video[]
  isLoading: boolean
  error: string | null
}

export const useVideoLibrary = () => {
  const [state, setState] = useState<VideoLibraryState>({
    videos: [],
    isLoading: false,
    error: null
  })

  const loadVideos = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const response = await apiClient.getVideos()
      
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch videos')
      }

      setState(prev => ({ 
        ...prev, 
        videos: Array.isArray(response.data) ? response.data : [],
        isLoading: false 
      }))
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Unknown error',
        isLoading: false 
      }))
    }
  }, [])

  const deleteVideo = useCallback(async (videoId: string) => {
    try {
      const response = await apiClient.deleteVideo(videoId)
      
      if (!response.success) {
        throw new Error(response.error || 'Failed to delete video')
      }

      // Remove video from state
      setState(prev => ({
        ...prev,
        videos: prev.videos.filter(video => video.id !== videoId)
      }))

      return true
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Unknown error'
      }))
      return false
    }
  }, [])

  const getDownloadUrl = useCallback((videoId: string) => {
    return apiClient.getDownloadUrl(videoId)
  }, [])

  const getInlineUrl = useCallback((videoId: string) => {
    return apiClient.getInlineUrl(videoId)
  }, [])

  const formatDuration = useCallback((seconds?: number) => {
    if (!seconds) return '0:00'
    
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }, [])

  const getStatusColor = useCallback((status: Video['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-600'
      case 'processing':
        return 'text-blue-600'
      case 'failed':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }, [])

  const getStatusText = useCallback((status: Video['status']) => {
    switch (status) {
      case 'completed':
        return 'Completed'
      case 'processing':
        return 'Processing'
      case 'failed':
        return 'Failed'
      case 'pending':
        return 'Pending'
      default:
        return 'Unknown'
    }
  }, [])

  // Auto-refresh videos every 10 seconds for processing videos
  useEffect(() => {
    const hasProcessingVideos = Array.isArray(state.videos) && state.videos.some(video => video.status === 'processing')
    
    if (hasProcessingVideos) {
      const interval = setInterval(loadVideos, 10000)
      return () => clearInterval(interval)
    }
  }, [state.videos, loadVideos])

  // Initial load
  useEffect(() => {
    loadVideos()
  }, [loadVideos])

  return {
    ...state,
    loadVideos,
    deleteVideo,
    getDownloadUrl,
    getInlineUrl,
    formatDuration,
    getStatusColor,
    getStatusText
  }
} 