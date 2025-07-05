import { useState, useEffect, useCallback } from 'react'
import { apiClient, Video, VideoProgress } from '../api'

export interface VideoCreationState {
  video: Video | null
  progress: VideoProgress[]
  isLoading: boolean
  error: string | null
  currentStep: number
  stepMapping: Record<string, number>
  // Add new progress state
  progressMessage: string | null
  progressPercent: number
  isProcessing: boolean
}

export interface VideoCreationHook extends VideoCreationState {
  createVideo: (title: string, description: string) => Promise<Video>
  subscribeToUpdates: (videoId: string) => () => void
  loadProgress: (videoId: string) => Promise<void>
  setCurrentStep: (step: number) => void
  reset: () => void
}

export const useVideoCreation = (): VideoCreationHook => {
  const [state, setState] = useState<VideoCreationState>({
    video: null,
    progress: [],
    isLoading: false,
    error: null,
    currentStep: 1,
    stepMapping: {
      start: 1,
      pending: 1,
      scene_generation: 2,
      scene_critique: 2,
      scene_critique_retry: 2,
      audio_generation: 3,
      video_assembly: 4,
      completed: 4,
      failed: 4
    },
    progressMessage: null,
    progressPercent: 0,
    isProcessing: false
  })

  const createVideo = useCallback(async (title: string, description: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const response = await apiClient.createVideo(title, description)
      
      if (!response.success) {
        throw new Error(response.error || 'Failed to create video')
      }

      const video = response.data!
      setState(prev => ({ 
        ...prev, 
        video,
        currentStep: prev.stepMapping[video.current_step] || 2, // Start at step 2 after video creation
        isLoading: false,
        isProcessing: video.status === 'processing',
        progressPercent: video.progress_percent || video.progress || 0
      }))

      return video
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Unknown error',
        isLoading: false 
      }))
      throw error
    }
  }, [])

  const subscribeToUpdates = useCallback((videoId: string) => {
    console.log('🔌 Starting SSE connection for video:', videoId)
    const eventSource = apiClient.createEventSource(videoId)
    
    eventSource.onopen = () => {
      console.log('✅ SSE connection opened for video:', videoId)
    }
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('SSE Event received:', data) // Debug log
        
        switch (data.type) {
          case 'progress':
            // Handle detailed progress updates
            console.log('Progress update:', data.message, data.progress) // Debug log
            setState(prev => ({
              ...prev,
              progressMessage: data.message || null,
              progressPercent: data.progress || prev.progressPercent,
              isProcessing: true
            }))
            break
            
          case 'status':
          case 'update':
            const updatedVideo = data.data as Video
            console.log('Video status update:', updatedVideo.current_step, updatedVideo.status) // Debug log
            setState(prev => ({
              ...prev,
              video: updatedVideo,
              currentStep: prev.stepMapping[updatedVideo.current_step] || prev.currentStep,
              progressPercent: updatedVideo.progress_percent || updatedVideo.progress || prev.progressPercent,
              isProcessing: updatedVideo.status === 'processing'
            }))
            break
            
          case 'complete':
            const completedVideo = data.data as Video
            console.log('Video completed:', completedVideo.id, completedVideo.status) // Debug log
            setState(prev => ({
              ...prev,
              video: completedVideo,
              currentStep: prev.stepMapping[completedVideo.current_step] || 4,
              isLoading: false,
              isProcessing: false,
              progressMessage: 'Video generation complete!',
              progressPercent: 100
            }))
            eventSource.close()
            break
            
          case 'error':
            setState(prev => ({
              ...prev,
              error: data.message || 'Unknown error occurred',
              isLoading: false,
              isProcessing: false,
              progressMessage: null
            }))
            eventSource.close()
            break
            
          case 'heartbeat':
            // Keep connection alive
            break
        }
      } catch (error) {
        console.error('Error parsing SSE data:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      setState(prev => ({
        ...prev,
        error: 'Connection lost. Please refresh the page.',
        isLoading: false,
        isProcessing: false
      }))
      eventSource.close()
    }

    return () => eventSource.close()
  }, [])

  const loadProgress = useCallback(async (videoId: string) => {
    try {
      const response = await apiClient.getVideoProgress(videoId)
      if (response.success) {
        setState(prev => ({ ...prev, progress: response.data! }))
      }
    } catch (error) {
      console.error('Error loading progress:', error)
    }
  }, [])

  const setCurrentStep = useCallback((step: number) => {
    setState(prev => ({ ...prev, currentStep: step }))
  }, [])

  const reset = useCallback(() => {
    setState({
      video: null,
      progress: [],
      isLoading: false,
      error: null,
      currentStep: 1,
      stepMapping: {
        start: 1,
        pending: 1,
        scene_generation: 2,
        scene_critique: 2,
        scene_critique_retry: 2,
        audio_generation: 3,
        video_assembly: 4,
        completed: 4,
        failed: 4
      },
      progressMessage: null,
      progressPercent: 0,
      isProcessing: false
    })
  }, [])

  return {
    ...state,
    createVideo,
    subscribeToUpdates,
    loadProgress,
    setCurrentStep,
    reset
  }
} 